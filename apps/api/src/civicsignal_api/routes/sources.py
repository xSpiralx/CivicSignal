import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.ingestion import ApprovedSource, SourceApprovalStatus
from civicsignal_api.policy import Permission
from civicsignal_api.schemas.ingestion import SourceCreate, SourceDecision, SourceView

router = APIRouter(prefix="/api/v1/admin/sources", tags=["source governance"])
Database = Annotated[AsyncSession, Depends(get_session)]
SourceManager = Annotated[AuthContext, Depends(require(Permission.ADMIN_MANAGE))]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]


@router.get("", response_model=list[SourceView])
async def list_sources(
    db: Database,
    auth: SourceManager,
    approval_status: Annotated[SourceApprovalStatus | None, Query()] = None,
) -> list[ApprovedSource]:
    query = select(ApprovedSource).order_by(ApprovedSource.name).limit(200)
    if approval_status is not None:
        query = query.where(ApprovedSource.approval_status == approval_status)
    return list(await db.scalars(query))


@router.post("", response_model=SourceView, status_code=201)
async def create_source(
    payload: SourceCreate,
    db: Database,
    csrf: CsrfAuth,
    auth: SourceManager,
) -> ApprovedSource:
    if await db.scalar(
        select(ApprovedSource.id).where(
            ApprovedSource.stable_identifier == payload.stable_identifier
        )
    ):
        raise HTTPException(409, "Source identifier already exists")
    values = payload.model_dump(mode="json", exclude={"automation_permission", "allowed_hosts"})
    source = ApprovedSource(
        **values,
        approval_status=SourceApprovalStatus.PROPOSED,
        enabled=False,
        automation_permission=False,
        allowed_hosts=[],
    )
    db.add(source)
    await db.flush()
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="source.propose",
            subject_type="approved_source",
            subject_id=str(source.id),
            summary=f"Proposed source {source.stable_identifier}; automation disabled",
        )
    )
    await db.commit()
    await db.refresh(source)
    return source


@router.put("/{source_id}/decision", response_model=SourceView)
async def decide_source(
    source_id: uuid.UUID,
    payload: SourceDecision,
    db: Database,
    csrf: CsrfAuth,
    auth: SourceManager,
) -> ApprovedSource:
    source = await db.get(ApprovedSource, source_id)
    if source is None:
        raise HTTPException(404, "Source not found")
    previous = source.approval_status
    source.approval_status = payload.approval_status
    source.enabled = payload.enabled
    source.automation_permission = payload.automation_permission
    source.allowed_hosts = sorted({host.strip().casefold() for host in payload.allowed_hosts})
    source.rate_limit = payload.rate_limit
    source.license_name = payload.license_name
    source.license_url = str(payload.license_url) if payload.license_url else None
    source.terms_url = str(payload.terms_url) if payload.terms_url else None
    source.attribution_requirement = payload.attribution_requirement
    source.redistribution_permitted = payload.redistribution_permitted
    source.modification_permitted = payload.modification_permitted
    source.last_legal_review_at = payload.last_legal_review_at
    source.last_technical_review_at = payload.last_technical_review_at
    source.reviewer_id = auth.account.id
    source.notes = payload.reason
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action=f"source.{payload.approval_status.value}",
            subject_type="approved_source",
            subject_id=str(source.id),
            summary=(
                f"Source decision {previous.value} -> {payload.approval_status.value}; "
                f"enabled={payload.enabled}. {payload.reason}"
            )[:500],
        )
    )
    await db.commit()
    await db.refresh(source)
    return source
