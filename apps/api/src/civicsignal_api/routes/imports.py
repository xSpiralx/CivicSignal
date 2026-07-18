import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import GovernedResource, ResourceRevision, WorkflowState
from civicsignal_api.models.ingestion import (
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
    if candidate.review_status != CandidateReviewStatus.PENDING:
        raise HTTPException(409, "Candidate was already reviewed")
    if candidate.duplicate_classification != "new_resource":
        raise HTTPException(409, "Duplicate or conflict candidates require explicit resolution")
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
