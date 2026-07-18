import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.geography import US_REGIONS
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import GovernedResource, ResourceRevision, WorkflowState
from civicsignal_api.models.ingestion import (
    ApprovedSource,
    CandidateResource,
    CandidateReviewStatus,
    ImportBatch,
    ImportBatchStatus,
)
from civicsignal_api.policy import Permission
from civicsignal_api.routes.governance import view
from civicsignal_api.schemas.governance import DraftContent, GovernedResourceView

router = APIRouter(prefix="/api/v1/admin/imports", tags=["governed imports"])
Database = Annotated[AsyncSession, Depends(get_session)]
Viewer = Annotated[AuthContext, Depends(require(Permission.RESOURCE_VIEW))]
Creator = Annotated[AuthContext, Depends(require(Permission.RESOURCE_DRAFT_CREATE))]
Canceller = Annotated[AuthContext, Depends(require(Permission.ADMIN_MANAGE))]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]


class CandidateAction(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=2000)
    high_risk_confirmed: bool = False
    assigned_reviewer_id: uuid.UUID | None = None
    governed_resource_id: uuid.UUID | None = None


class CandidateEdit(BaseModel):
    expected_version: int = Field(ge=1)
    content: DraftContent


class BulkAction(BaseModel):
    candidate_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    action: str
    reason: str = Field(min_length=3, max_length=2000)
    assigned_reviewer_id: uuid.UUID | None = None


def candidate_view(
    item: CandidateResource, source: ApprovedSource, batch: ImportBatch
) -> dict[str, Any]:
    return {
        "id": item.id,
        "batch_id": item.batch_id,
        "source_id": item.source_id,
        "source_identifier": item.source_identifier,
        "source": {
            "stable_identifier": source.stable_identifier,
            "name": source.name,
            "publishing_organization": source.publishing_organization,
            "source_url": source.source_url,
            "license_name": source.license_name,
            "license_url": source.license_url,
            "attribution_requirement": source.attribution_requirement,
        },
        "content": item.content,
        "raw_content": item.raw_content,
        "source_url": item.source_url,
        "source_record_updated_at": item.source_record_updated_at,
        "dataset_updated_at": item.dataset_updated_at,
        "retrieved_at": item.retrieved_at,
        "city": item.city,
        "county": item.county,
        "region": item.region,
        "postal_code": item.postal_code,
        "categories": item.categories,
        "service_area_type": item.service_area_type,
        "nationwide": item.nationwide,
        "remote": item.remote,
        "risk_classification": item.risk_classification,
        "duplicate_classification": item.duplicate_classification,
        "conflict_status": item.conflict_status,
        "validation_status": item.validation_status,
        "validation_result": item.validation_result,
        "review_status": item.review_status.value,
        "reviewer_id": item.reviewer_id,
        "review_decision": item.review_decision,
        "governed_resource_id": item.governed_resource_id,
        "version": item.version,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "batch": {"status": batch.status.value, "created_at": batch.created_at},
    }


@router.get("/candidates")
async def nationwide_candidates(
    db: Database,
    auth: Viewer,
    q: Annotated[str | None, Query(max_length=200)] = None,
    state: Annotated[str | None, Query(max_length=120)] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    county: Annotated[str | None, Query(max_length=160)] = None,
    postal_code: Annotated[str | None, Query(max_length=30)] = None,
    category: Annotated[str | None, Query(max_length=120)] = None,
    source: Annotated[str | None, Query(max_length=120)] = None,
    batch_id: uuid.UUID | None = None,
    review_status: CandidateReviewStatus | None = None,
    duplicate_status: Annotated[str | None, Query(max_length=50)] = None,
    conflict_status: Annotated[str | None, Query(max_length=50)] = None,
    risk: Annotated[str | None, Query(max_length=30)] = None,
    assigned_reviewer_id: uuid.UUID | None = None,
    nationwide: bool | None = None,
    remote: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, Any]:
    filters: list[Any] = []
    if q:
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                CandidateResource.source_identifier.ilike(term),
                CandidateResource.city.ilike(term),
                CandidateResource.county.ilike(term),
                CandidateResource.content["organization_name"].as_string().ilike(term),
                CandidateResource.content["service_name"].as_string().ilike(term),
            )
        )
    for value, column in (
        (state, CandidateResource.region),
        (city, CandidateResource.city),
        (county, CandidateResource.county),
        (postal_code, CandidateResource.postal_code),
        (duplicate_status, CandidateResource.duplicate_classification),
        (conflict_status, CandidateResource.conflict_status),
        (risk, CandidateResource.risk_classification),
    ):
        if value:
            filters.append(func.lower(column) == value.strip().casefold())
    if category:
        filters.append(CandidateResource.categories.contains([category]))
    if source:
        filters.append(ApprovedSource.stable_identifier == source)
    if batch_id:
        filters.append(CandidateResource.batch_id == batch_id)
    if review_status:
        filters.append(CandidateResource.review_status == review_status)
    if assigned_reviewer_id:
        filters.append(CandidateResource.reviewer_id == assigned_reviewer_id)
    if nationwide is not None:
        filters.append(CandidateResource.nationwide == nationwide)
    if remote is not None:
        filters.append(CandidateResource.remote == remote)
    joined = (
        select(CandidateResource, ApprovedSource, ImportBatch)
        .join(ApprovedSource, CandidateResource.source_id == ApprovedSource.id)
        .join(ImportBatch, CandidateResource.batch_id == ImportBatch.id)
        .where(*filters)
    )
    total = int(await db.scalar(select(func.count()).select_from(joined.subquery())) or 0)
    rows = (
        await db.execute(
            joined.order_by(
                CandidateResource.risk_classification.desc(),
                CandidateResource.region.asc().nullslast(),
                CandidateResource.city.asc().nullslast(),
                CandidateResource.created_at.asc(),
                CandidateResource.id.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {
        "items": [candidate_view(item, item_source, batch) for item, item_source, batch in rows],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/candidates/{candidate_id}")
async def candidate_detail(candidate_id: uuid.UUID, db: Database, auth: Viewer) -> dict[str, Any]:
    row = (
        await db.execute(
            select(CandidateResource, ApprovedSource, ImportBatch)
            .join(ApprovedSource, CandidateResource.source_id == ApprovedSource.id)
            .join(ImportBatch, CandidateResource.batch_id == ImportBatch.id)
            .where(CandidateResource.id == candidate_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "Candidate not found")
    item, source, batch = row
    result = candidate_view(item, source, batch)
    audits = list(
        await db.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.subject_type == "candidate_resource",
                AuditEvent.subject_id == str(item.id),
            )
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
        )
    )
    result["audit_history"] = [
        {"action": audit.action, "summary": audit.summary, "created_at": audit.created_at}
        for audit in audits
    ]
    return result


@router.put("/candidates/{candidate_id}")
async def edit_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateEdit,
    db: Database,
    csrf: CsrfAuth,
    auth: Creator,
) -> dict[str, Any]:
    item = await db.get(CandidateResource, candidate_id)
    if item is None:
        raise HTTPException(404, "Candidate not found")
    if item.version != payload.expected_version:
        raise HTTPException(409, "Candidate changed; reload before saving")
    if item.review_status in {
        CandidateReviewStatus.ACCEPTED_AS_DRAFT,
        CandidateReviewStatus.MERGED,
        CandidateReviewStatus.REJECTED,
    }:
        raise HTTPException(409, "Reviewed candidate is no longer editable")
    item.content = payload.content.model_dump(mode="json")
    item.city = payload.content.city
    item.region = payload.content.region
    item.postal_code = payload.content.postal_code
    item.categories = payload.content.categories
    item.remote = payload.content.remote_service_available
    item.review_status = CandidateReviewStatus.READY_FOR_REVIEW
    item.version += 1
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="import.candidate.edit",
            subject_type="candidate_resource",
            subject_id=str(item.id),
            summary="Candidate normalized content edited; source projection retained",
        )
    )
    await db.commit()
    return {"id": item.id, "review_status": item.review_status.value, "version": item.version}


@router.get("/dashboard")
async def import_dashboard(db: Database, auth: Viewer) -> dict[str, Any]:
    total = int(await db.scalar(select(func.count(CandidateResource.id))) or 0)

    async def grouped(column: Any) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                select(column, func.count()).group_by(column).order_by(func.count().desc())
            )
        ).all()
        return [{"key": key or "Unknown", "count": count} for key, count in rows]

    return {
        "total": total,
        "ready_for_review": int(
            await db.scalar(
                select(func.count())
                .where(CandidateResource.review_status == CandidateReviewStatus.READY_FOR_REVIEW)
                .select_from(CandidateResource)
            )
            or 0
        ),
        "high_risk": int(
            await db.scalar(
                select(func.count())
                .where(CandidateResource.risk_classification == "high")
                .select_from(CandidateResource)
            )
            or 0
        ),
        "possible_duplicates": int(
            await db.scalar(
                select(func.count())
                .where(CandidateResource.duplicate_classification != "new_resource")
                .select_from(CandidateResource)
            )
            or 0
        ),
        "conflicts": int(
            await db.scalar(
                select(func.count())
                .where(CandidateResource.conflict_status != "none")
                .select_from(CandidateResource)
            )
            or 0
        ),
        "by_state": await grouped(CandidateResource.region),
        "by_city": (await grouped(CandidateResource.city))[:100],
        "by_status": await grouped(CandidateResource.review_status),
        "by_risk": await grouped(CandidateResource.risk_classification),
    }


@router.get("/coverage")
async def source_coverage(db: Database, auth: Viewer) -> dict[str, Any]:
    count_rows = (
        await db.execute(
            select(CandidateResource.region, func.count()).group_by(CandidateResource.region)
        )
    ).all()
    counts: dict[str, int] = {code: int(count) for code, count in count_rows if code}
    return {
        "states": [
            {
                "code": code,
                "name": name,
                "candidate_count": int(counts.get(code, 0)),
                "status": "awaiting_review" if counts.get(code, 0) else "not_started",
            }
            for code, name in US_REGIONS.items()
            if code not in {"AS", "GU", "MP", "PR", "VI"}
        ],
        "territories": [
            {
                "code": code,
                "name": name,
                "candidate_count": int(counts.get(code, 0)),
                "status": "awaiting_review" if counts.get(code, 0) else "not_started",
            }
            for code, name in US_REGIONS.items()
            if code in {"AS", "GU", "MP", "PR", "VI"}
        ],
    }


@router.get("/{batch_id}/candidates")
async def list_candidates(batch_id: uuid.UUID, db: Database, auth: Viewer) -> list[dict[str, Any]]:
    if await db.get(ImportBatch, batch_id) is None:
        raise HTTPException(404, "Import batch not found")
    candidates = list(
        await db.scalars(
            select(CandidateResource)
            .where(CandidateResource.batch_id == batch_id)
            .order_by(CandidateResource.created_at)
            .limit(1_000)
        )
    )
    return [
        {
            "id": item.id,
            "source_identifier": item.source_identifier,
            "content": item.content,
            "duplicate_classification": item.duplicate_classification,
            "validation_result": item.validation_result,
            "review_status": item.review_status.value,
            "governed_resource_id": item.governed_resource_id,
        }
        for item in candidates
    ]


@router.post("/candidates/{candidate_id}/{action}")
async def review_candidate(
    candidate_id: uuid.UUID,
    action: str,
    payload: CandidateAction,
    db: Database,
    csrf: CsrfAuth,
    auth: Creator,
) -> dict[str, Any]:
    item = await db.get(CandidateResource, candidate_id)
    if item is None:
        raise HTTPException(404, "Candidate not found")
    if item.version != payload.expected_version:
        raise HTTPException(409, "Candidate changed; reload before continuing")
    allowed = {
        "claim",
        "release",
        "defer",
        "reject",
        "request-source-review",
        "mark-duplicate",
        "needs-normalization",
        "needs-content-review",
        "assign",
        "merge",
    }
    if action not in allowed:
        raise HTTPException(404, "Candidate action not found")
    if (
        action in {"defer", "reject", "request-source-review", "mark-duplicate"}
        and not payload.reason
    ):
        raise HTTPException(422, "A reason is required")
    if action == "claim":
        if item.reviewer_id and item.reviewer_id != auth.account.id:
            raise HTTPException(409, "Candidate is already claimed")
        item.reviewer_id = auth.account.id
        item.review_status = CandidateReviewStatus.CLAIMED
    elif action == "release":
        if item.reviewer_id not in {None, auth.account.id}:
            raise HTTPException(409, "Only the assigned reviewer may release this candidate")
        item.reviewer_id = None
        item.review_status = CandidateReviewStatus.READY_FOR_REVIEW
    elif action == "defer":
        item.review_status = CandidateReviewStatus.DEFERRED
    elif action == "reject":
        item.review_status = CandidateReviewStatus.REJECTED
    elif action == "request-source-review":
        item.review_status = CandidateReviewStatus.NEEDS_SOURCE_REVIEW
    elif action == "mark-duplicate":
        item.review_status = CandidateReviewStatus.REJECTED
        item.duplicate_classification = "exact_match"
    elif action == "needs-normalization":
        item.review_status = CandidateReviewStatus.NEEDS_NORMALIZATION
    elif action == "needs-content-review":
        item.review_status = CandidateReviewStatus.NEEDS_CONTENT_REVIEW
    elif action == "assign":
        item.reviewer_id = payload.assigned_reviewer_id
    elif action == "merge":
        if payload.governed_resource_id is None:
            raise HTTPException(422, "An existing governed resource is required")
        if await db.get(GovernedResource, payload.governed_resource_id) is None:
            raise HTTPException(404, "Governed resource not found")
        item.governed_resource_id = payload.governed_resource_id
        item.review_status = CandidateReviewStatus.MERGED
    item.review_decision = payload.reason
    item.version += 1
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action=f"import.candidate.{action}",
            subject_type="candidate_resource",
            subject_id=str(item.id),
            summary=f"Candidate review action: {action}",
        )
    )
    await db.commit()
    return {
        "id": item.id,
        "review_status": item.review_status.value,
        "reviewer_id": item.reviewer_id,
        "version": item.version,
    }


@router.post("/candidates/bulk")
async def bulk_review(
    payload: BulkAction, db: Database, csrf: CsrfAuth, auth: Creator
) -> dict[str, Any]:
    if payload.action not in {
        "assign",
        "defer",
        "reject-exact-duplicates",
        "source-review",
        "normalization-review",
    }:
        raise HTTPException(422, "Bulk action is not permitted")
    items = list(
        await db.scalars(
            select(CandidateResource).where(CandidateResource.id.in_(payload.candidate_ids))
        )
    )
    if len(items) != len(set(payload.candidate_ids)):
        raise HTTPException(404, "One or more candidates were not found")
    for item in items:
        if item.risk_classification == "high" and payload.action == "reject-exact-duplicates":
            raise HTTPException(409, "High-risk candidates cannot be bulk-rejected")
        if payload.action == "assign":
            item.reviewer_id = payload.assigned_reviewer_id
        elif payload.action == "defer":
            item.review_status = CandidateReviewStatus.DEFERRED
        elif payload.action == "reject-exact-duplicates":
            if item.duplicate_classification != "exact_match":
                raise HTTPException(409, "Bulk rejection is limited to exact duplicates")
            item.review_status = CandidateReviewStatus.REJECTED
        elif payload.action == "source-review":
            item.review_status = CandidateReviewStatus.NEEDS_SOURCE_REVIEW
        else:
            item.review_status = CandidateReviewStatus.NEEDS_NORMALIZATION
        item.review_decision = payload.reason
        item.version += 1
        db.add(
            AuditEvent(
                actor_id=auth.account.id,
                action=f"import.candidate.bulk.{payload.action}",
                subject_type="candidate_resource",
                subject_id=str(item.id),
                summary=f"Bulk review action: {payload.action}",
            )
        )
    await db.commit()
    return {"updated": len(items), "action": payload.action}


@router.post("/{batch_id}/cancel", status_code=204)
async def cancel_batch(
    batch_id: uuid.UUID,
    db: Database,
    csrf: CsrfAuth,
    auth: Canceller,
) -> None:
    batch = await db.get(ImportBatch, batch_id)
    if batch is None:
        raise HTTPException(404, "Import batch not found")
    if batch.status not in {ImportBatchStatus.PENDING, ImportBatchStatus.NEEDS_REVIEW}:
        raise HTTPException(409, "Import batch cannot be cancelled in its current state")
    accepted = await db.scalar(
        select(CandidateResource.id).where(
            CandidateResource.batch_id == batch_id,
            CandidateResource.review_status == CandidateReviewStatus.ACCEPTED_AS_DRAFT,
        )
    )
    if accepted:
        raise HTTPException(409, "Import batch has accepted drafts and cannot be cancelled")
    batch.status = ImportBatchStatus.CANCELLED
    batch.review_decision = "Cancelled by an administrator; candidates retained for audit"
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="import.batch.cancel",
            subject_type="import_batch",
            subject_id=str(batch.id),
            summary="Import batch cancelled; no draft or public record was created",
        )
    )
    await db.commit()


@router.post("/{batch_id}/candidates/{candidate_id}/accept", response_model=GovernedResourceView)
async def accept_candidate_as_draft(
    batch_id: uuid.UUID,
    candidate_id: uuid.UUID,
    db: Database,
    csrf: CsrfAuth,
    auth: Creator,
    high_risk_confirmed: bool = False,
) -> GovernedResourceView:
    batch = await db.get(ImportBatch, batch_id)
    if batch is None:
        raise HTTPException(404, "Import batch not found")
    if batch.status != ImportBatchStatus.NEEDS_REVIEW:
        raise HTTPException(409, "Import batch is not open for human review")
    candidate = await db.scalar(
        select(CandidateResource).where(
            CandidateResource.id == candidate_id,
            CandidateResource.batch_id == batch_id,
        )
    )
    if candidate is None:
        raise HTTPException(404, "Candidate not found")
    if candidate.review_status not in {
        CandidateReviewStatus.READY_FOR_REVIEW,
        CandidateReviewStatus.CLAIMED,
    }:
        raise HTTPException(409, "Candidate was already reviewed")
    if candidate.duplicate_classification != "new_resource":
        raise HTTPException(409, "Duplicate or conflict candidates require explicit resolution")
    if candidate.risk_classification == "high" and not high_risk_confirmed:
        raise HTTPException(409, "High-risk candidates require the confirmed approval endpoint")
    try:
        content = DraftContent.model_validate(candidate.content)
    except ValidationError as exc:
        raise HTTPException(422, "Candidate no longer passes the draft schema") from exc
    resource = GovernedResource(state=WorkflowState.DRAFT, owner_id=auth.account.id)
    db.add(resource)
    await db.flush()
    revision = ResourceRevision(
        resource_id=resource.id,
        number=1,
        content=content.model_dump(mode="json"),
        created_by_id=auth.account.id,
    )
    db.add(revision)
    await db.flush()
    resource.current_revision_id = revision.id
    candidate.review_status = CandidateReviewStatus.ACCEPTED_AS_DRAFT
    candidate.reviewer_id = auth.account.id
    candidate.governed_resource_id = resource.id
    candidate.review_decision = "Accepted by a human reviewer as a governed draft"
    candidate.version += 1
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="import.candidate.accept_as_draft",
            subject_type="candidate_resource",
            subject_id=str(candidate.id),
            summary=f"Candidate accepted as governed draft {resource.id}; not published",
        )
    )
    await db.commit()
    return await view(db, resource)
