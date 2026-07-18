from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.policy import Permission
from civicsignal_api.schemas.auth import AuditEventView

router = APIRouter(prefix="/api/v1/admin/audit", tags=["audit"])
Database = Annotated[AsyncSession, Depends(get_session)]
AuditViewer = Annotated[AuthContext, Depends(require(Permission.AUDIT_VIEW))]


@router.get("", response_model=list[AuditEventView])
async def list_audit_events(
    db: Database,
    auth: AuditViewer,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AuditEventView]:
    events = list(
        await db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit))
    )
    return [AuditEventView.model_validate(event) for event in events]
