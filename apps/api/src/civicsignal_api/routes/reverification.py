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
from civicsignal_api.schemas.corrections import ReverificationAction, ReverificationView
from civicsignal_api.security import utcnow
from civicsignal_api.services.governance import current_revision, publish

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
        if (
            not payload.evidence_summary
            or not payload.source_references
            or not payload.proposed_content
        ):
            raise HTTPException(422, "Evidence, sources, and proposed content are required")
        resource = await db.get(GovernedResource, task.resource_id)
        if not resource:
            raise HTTPException(409, "Governed resource is unavailable")
        previous = await current_revision(db, resource)
        if payload.expected_revision != previous.number:
            raise HTTPException(409, "Resource changed; reload before continuing")
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
                resource = await db.get(GovernedResource, task.resource_id)
                if resource:
                    resource.state = WorkflowState.ARCHIVED
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
