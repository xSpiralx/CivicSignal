import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import (
    CorrectionReport,
    CorrectionStatus,
    GovernedResource,
    ResourceRevision,
    ReverificationOutcome,
    ReverificationStatus,
    ReverificationTask,
    WorkflowState,
)
from civicsignal_api.models.resource import Service, Verification, VerificationStatus
from civicsignal_api.policy import Permission, permissions_for
from civicsignal_api.schemas.corrections import (
    ProposalSave,
    ProposalView,
    ReverificationAction,
    ReverificationView,
)
from civicsignal_api.schemas.governance import DraftContent
from civicsignal_api.security import utcnow
from civicsignal_api.services.governance import publish

router = APIRouter(prefix="/api/v1/admin/reverification", tags=["re-verification"])
Database = Annotated[AsyncSession, Depends(get_session)]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]


async def _load(
    db: AsyncSession, task_id: uuid.UUID, *, for_update: bool = False
) -> ReverificationTask:
    statement = select(ReverificationTask).where(ReverificationTask.id == task_id)
    if for_update:
        statement = statement.with_for_update()
    task = await db.scalar(statement)
    if not task:
        raise HTTPException(404, "Re-verification task not found")
    return task


@router.get("", response_model=list[ReverificationView])
async def list_tasks(
    db: Database,
    auth: Annotated[AuthContext, Depends(require(Permission.REVERIFICATION_VIEW))],
    status: ReverificationStatus | None = None,
    freshness: str | None = None,
    assigned_to_me: bool = False,
    offset: int = 0,
    limit: int = 50,
) -> list[ReverificationView]:
    statement = select(ReverificationTask).order_by(
        ReverificationTask.due_at.asc(), ReverificationTask.created_at.asc()
    )
    if status:
        statement = statement.where(ReverificationTask.status == status)
    if freshness:
        statement = statement.where(ReverificationTask.freshness_state == freshness)
    if assigned_to_me:
        statement = statement.where(ReverificationTask.assigned_verifier_id == auth.account.id)
    tasks = (await db.scalars(statement.offset(max(offset, 0)).limit(min(limit, 100)))).all()
    return [ReverificationView.model_validate(item) for item in tasks]


@router.get("/{task_id}", response_model=ReverificationView)
async def get_task(
    task_id: uuid.UUID,
    db: Database,
    auth: Annotated[AuthContext, Depends(require(Permission.REVERIFICATION_VIEW))],
) -> ReverificationView:
    return ReverificationView.model_validate(await _load(db, task_id))


def _proposal_view(
    task: ReverificationTask,
    resource: GovernedResource,
    published: ResourceRevision,
    proposed: ResourceRevision,
) -> ProposalView:
    published_content = DraftContent.model_validate(published.content)
    proposed_content = DraftContent.model_validate(proposed.content)
    before = published_content.model_dump(mode="json")
    after = proposed_content.model_dump(mode="json")
    changed = [key for key in before if before[key] != after[key]]
    blockers: list[str] = []
    warnings: list[str] = []
    if not proposed_content.categories:
        blockers.append("Add at least one category.")
    if not any(
        (
            proposed_content.contact_phone,
            proposed_content.contact_email,
            proposed_content.website,
            proposed_content.application_instructions,
        )
    ):
        blockers.append("Add at least one contact or service-access method.")
    if not any(
        (
            proposed_content.location_name,
            proposed_content.city,
            proposed_content.postal_code,
            proposed_content.service_area,
            proposed_content.remote_service_available,
        )
    ):
        blockers.append("Add a location, service area, or remote-service indication.")
    if not proposed_content.hours:
        blockers.append("Add hours or explicitly describe that hours vary.")
    if not proposed_content.source_supports_changed_fields:
        blockers.append("Confirm that the source supports the changed fields.")
    if proposed_content.eligibility is None:
        warnings.append("Eligibility is unspecified.")
    if not changed:
        warnings.append("The proposal has no changes from the published revision.")
    return ProposalView(
        task_id=task.id,
        task_version=task.version,
        resource_id=resource.id,
        published_revision=published.number,
        proposed_revision=proposed.number,
        published_content=published_content,
        proposed_content=proposed_content,
        changed_fields=changed,
        blocking_errors=blockers,
        warnings=warnings,
        ready=not blockers and bool(changed),
    )


async def _proposal_records(
    db: AsyncSession, task: ReverificationTask
) -> tuple[GovernedResource, ResourceRevision, ResourceRevision]:
    resource = await db.get(GovernedResource, task.resource_id)
    if not resource or not resource.published_revision_id:
        raise HTTPException(409, "Published governed resource is unavailable")
    published = await db.get(ResourceRevision, resource.published_revision_id)
    proposed = await db.get(ResourceRevision, resource.current_revision_id)
    if not published or not proposed:
        raise HTTPException(409, "Resource revision is unavailable")
    return resource, published, proposed


@router.get("/{task_id}/proposal", response_model=ProposalView)
async def get_proposal(
    task_id: uuid.UUID,
    db: Database,
    auth: Annotated[AuthContext, Depends(require(Permission.REVERIFICATION_VIEW))],
) -> ProposalView:
    task = await _load(db, task_id)
    return _proposal_view(task, *(await _proposal_records(db, task)))


@router.post("/{task_id}/proposal", response_model=ProposalView)
async def save_proposal(
    task_id: uuid.UUID, payload: ProposalSave, db: Database, csrf: CsrfAuth
) -> ProposalView:
    if Permission.REVERIFICATION_OPERATE not in permissions_for(csrf.account):
        raise HTTPException(403, "Permission denied")
    task = await _load(db, task_id, for_update=True)
    if not task.active:
        raise HTTPException(409, "Task is closed")
    if task.version != payload.expected_task_version:
        raise HTTPException(409, "Task changed; reload before saving")
    resource, published, current = await _proposal_records(db, task)
    if current.number != payload.expected_revision:
        raise HTTPException(409, "Resource changed; reload before saving")
    number = (
        int(
            await db.scalar(
                select(func.max(ResourceRevision.number)).where(
                    ResourceRevision.resource_id == resource.id
                )
            )
            or 0
        )
        + 1
    )
    proposed = ResourceRevision(
        resource_id=resource.id,
        number=number,
        content=payload.content.model_dump(mode="json"),
        created_by_id=csrf.account.id,
    )
    db.add(proposed)
    await db.flush()
    resource.current_revision_id = proposed.id
    task.version += 1
    db.add(
        AuditEvent(
            actor_id=csrf.account.id,
            action="reverification.proposal_saved",
            subject_type="reverification_task",
            subject_id=str(task.id),
            summary=f"Proposed resource revision {number} saved",
        )
    )
    await db.commit()
    await db.refresh(task)
    return _proposal_view(task, resource, published, proposed)


@router.post("/{task_id}/proposal/discard", response_model=ProposalView)
async def discard_proposal(
    task_id: uuid.UUID, payload: ReverificationAction, db: Database, csrf: CsrfAuth
) -> ProposalView:
    if Permission.REVERIFICATION_OPERATE not in permissions_for(csrf.account):
        raise HTTPException(403, "Permission denied")
    task = await _load(db, task_id, for_update=True)
    if task.version != payload.expected_version:
        raise HTTPException(409, "Task changed; reload before discarding")
    resource, published, current = await _proposal_records(db, task)
    resource.current_revision_id = published.id
    task.version += 1
    db.add(
        AuditEvent(
            actor_id=csrf.account.id,
            action="reverification.proposal_discarded",
            subject_type="reverification_task",
            subject_id=str(task.id),
            summary=f"Working revision {current.number} discarded; published revision restored",
        )
    )
    await db.commit()
    await db.refresh(task)
    return _proposal_view(task, resource, published, published)


@router.post("/{task_id}/{action}", response_model=ReverificationView)
async def act_on_task(
    task_id: uuid.UUID,
    action: str,
    payload: ReverificationAction,
    db: Database,
    csrf: CsrfAuth,
) -> ReverificationView:
    permission = (
        Permission.REVERIFICATION_ASSIGN
        if action == "assign"
        else Permission.REVERIFICATION_OPERATE
    )
    if permission not in permissions_for(csrf.account):
        raise HTTPException(403, "Permission denied")
    task = await _load(db, task_id, for_update=True)
    if task.version != payload.expected_version:
        raise HTTPException(409, "Task changed; reload before continuing")
    if not task.active and action not in {"reopen"}:
        raise HTTPException(409, "Task is closed")
    now = utcnow()
    if action == "claim":
        if task.assigned_verifier_id and task.assigned_verifier_id != csrf.account.id:
            raise HTTPException(409, "Task is already assigned")
        task.assigned_verifier_id = csrf.account.id
        task.claimed_at = now
        task.status = ReverificationStatus.CLAIMED
    elif action == "assign":
        if not payload.assignee_id:
            raise HTTPException(422, "An assignee is required")
        task.assigned_verifier_id = payload.assignee_id
        task.claimed_at = now
        task.status = ReverificationStatus.CLAIMED
    elif action == "release":
        task.assigned_verifier_id = None
        task.claimed_at = None
        task.status = ReverificationStatus.OPEN
    elif action == "start":
        if (
            task.assigned_verifier_id != csrf.account.id
            and Permission.ADMIN_MANAGE not in permissions_for(csrf.account)
        ):
            raise HTTPException(403, "Claim the task before starting")
        task.started_at = now
        task.status = ReverificationStatus.IN_PROGRESS
    elif action == "update-evidence":
        task.evidence_summary = payload.evidence_summary
        task.contact_attempt_summary = payload.contact_attempt_summary
        task.source_references = payload.source_references
        task.notes = payload.notes
    elif action == "updated-confirmed":
        if not payload.evidence_summary or not payload.source_references:
            raise HTTPException(422, "Evidence and source references are required")
        resource, published_revision, current = await _proposal_records(db, task)
        if payload.expected_revision != current.number:
            raise HTTPException(409, "Resource changed; reload before continuing")
        revision = current
        if payload.proposed_content:
            number = (
                int(
                    await db.scalar(
                        select(func.max(ResourceRevision.number)).where(
                            ResourceRevision.resource_id == resource.id
                        )
                    )
                    or 0
                )
                + 1
            )
            revision = ResourceRevision(
                resource_id=resource.id,
                number=number,
                content=payload.proposed_content.model_dump(mode="json"),
                created_by_id=csrf.account.id,
            )
            db.add(revision)
            await db.flush()
            resource.current_revision_id = revision.id
        if revision.id == published_revision.id:
            raise HTTPException(409, "Save a proposed revision before publishing")
        readiness = _proposal_view(task, resource, published_revision, revision)
        if not readiness.ready:
            raise HTTPException(
                422, "; ".join(readiness.blocking_errors) or "Proposal is not ready"
            )
        await publish(db, resource, revision, csrf.account, payload.next_due_at)
        resource.state = WorkflowState.PUBLISHED
        await _complete(db, task, ReverificationOutcome.UPDATED_CONFIRMED, payload, now)
    elif action in {
        "confirmed-unchanged",
        "could-not-confirm",
        "provider-unavailable",
        "source-unavailable",
        "resource-closed",
        "archive",
        "escalate",
        "cancel-duplicate",
    }:
        if not payload.evidence_summary and action not in {"cancel-duplicate"}:
            raise HTTPException(422, "An evidence summary is required")
        outcomes = {
            "confirmed-unchanged": ReverificationOutcome.CONFIRMED_UNCHANGED,
            "could-not-confirm": ReverificationOutcome.COULD_NOT_CONFIRM,
            "provider-unavailable": ReverificationOutcome.PROVIDER_UNAVAILABLE,
            "source-unavailable": ReverificationOutcome.SOURCE_UNAVAILABLE,
            "resource-closed": ReverificationOutcome.RESOURCE_CLOSED,
            "archive": ReverificationOutcome.ARCHIVED,
            "escalate": ReverificationOutcome.ESCALATED,
            "cancel-duplicate": None,
        }
        if action == "escalate":
            task.status = ReverificationStatus.ESCALATED
            task.outcome = ReverificationOutcome.ESCALATED
            task.notes = payload.reason
        elif action == "cancel-duplicate":
            task.status = ReverificationStatus.CANCELLED
            task.active = None
            task.completed_at = now
        else:
            outcome = outcomes[action]
            assert outcome is not None
            await _complete(db, task, outcome, payload, now)
            if action in {"resource-closed", "archive"}:
                service = await db.get(Service, task.service_id)
                if service:
                    service.is_active = False
                archived_resource = await db.get(GovernedResource, task.resource_id)
                if archived_resource:
                    archived_resource.state = WorkflowState.ARCHIVED
    else:
        raise HTTPException(404, "Unknown task action")
    task.version += 1
    db.add(
        AuditEvent(
            actor_id=csrf.account.id,
            action=f"reverification.{action}",
            subject_type="reverification_task",
            subject_id=str(task.id),
            summary=f"Re-verification action completed: {action}",
        )
    )
    await db.commit()
    await db.refresh(task)
    return ReverificationView.model_validate(task)


async def _complete(
    db: AsyncSession,
    task: ReverificationTask,
    outcome: ReverificationOutcome,
    payload: ReverificationAction,
    now: datetime,
) -> None:
    task.status = ReverificationStatus.COMPLETED
    task.outcome = outcome
    task.evidence_summary = payload.evidence_summary
    task.contact_attempt_summary = payload.contact_attempt_summary
    task.source_references = payload.source_references
    task.notes = payload.notes
    task.completed_at = now
    task.active = None
    if outcome == ReverificationOutcome.CONFIRMED_UNCHANGED:
        db.add(
            Verification(
                service_id=task.service_id,
                status=VerificationStatus.VERIFIED,
                checked_at=now,
                expires_at=payload.next_due_at or now + timedelta(days=90),
                checked_by="Governed re-verification",
                notes="Completed through re-verification workflow",
            )
        )
    if outcome in {
        ReverificationOutcome.CONFIRMED_UNCHANGED,
        ReverificationOutcome.UPDATED_CONFIRMED,
    }:
        reports = await db.scalars(
            select(CorrectionReport).where(
                CorrectionReport.task_id == task.id,
                CorrectionReport.status == CorrectionStatus.NEEDS_REVERIFICATION,
            )
        )
        for report in reports:
            report.status = CorrectionStatus.RESOLVED
            report.resolution_reason = f"Resolved by re-verification outcome {outcome.value}"
            report.resolved_at = now
            report.version += 1
