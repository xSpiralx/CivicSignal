import hashlib
import ipaddress
import time
import uuid
from collections import defaultdict, deque
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import (
    CorrectionReport,
    CorrectionStatus,
    GovernedResource,
    ReverificationStatus,
    ReverificationTask,
)
from civicsignal_api.policy import Permission, permissions_for
from civicsignal_api.schemas.corrections import (
    CorrectionAction,
    CorrectionView,
    PublicCorrectionCreate,
    PublicCorrectionResponse,
)
from civicsignal_api.security import utcnow
from civicsignal_api.services.resources import get_service

public_router = APIRouter(prefix="/api/v1/services", tags=["public corrections"])
admin_router = APIRouter(prefix="/api/v1/admin/corrections", tags=["correction governance"])
Database = Annotated[AsyncSession, Depends(get_session)]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]

_network_attempts: dict[str, deque[float]] = defaultdict(deque)
_resource_attempts: dict[str, deque[float]] = defaultdict(deque)


def _limited(bucket: deque[float], *, maximum: int, window: int) -> bool:
    now = time.monotonic()
    while bucket and bucket[0] < now - window:
        bucket.popleft()
    if len(bucket) >= maximum:
        return True
    bucket.append(now)
    return False


def _network_key(request: Request) -> str:
    raw = request.client.host if request.client else "unknown"
    try:
        address = ipaddress.ip_address(raw)
        network = ipaddress.ip_network(
            f"{address}/{24 if address.version == 4 else 64}", strict=False
        )
        return hashlib.sha256(str(network).encode()).hexdigest()
    except ValueError:
        return hashlib.sha256(raw.encode()).hexdigest()


def _correction_view(report: CorrectionReport, *, show_contact: bool) -> CorrectionView:
    view = CorrectionView.model_validate(report)
    if not show_contact:
        view.reporter_name = None
        view.reporter_email = None
    return view


@public_router.post(
    "/{service_id}/corrections", response_model=PublicCorrectionResponse, status_code=202
)
async def submit_correction(
    service_id: uuid.UUID, payload: PublicCorrectionCreate, request: Request, db: Database
) -> PublicCorrectionResponse:
    if payload.website:
        raise HTTPException(422, "Submission could not be accepted")
    if payload.form_started_at and (utcnow() - payload.form_started_at).total_seconds() < 2:
        raise HTTPException(422, "Please review the report before submitting")
    if _limited(_network_attempts[_network_key(request)], maximum=8, window=900) or _limited(
        _resource_attempts[str(service_id)], maximum=5, window=900
    ):
        raise HTTPException(429, "Too many reports; please try again later")
    if await get_service(db, service_id) is None:
        raise HTTPException(404, "Resource not found")
    normalized = " ".join(payload.description.casefold().split())
    fingerprint = hashlib.sha256(
        f"{service_id}:{payload.category.value}:{normalized}".encode()
    ).hexdigest()
    duplicate = await db.scalar(
        select(CorrectionReport.id).where(
            CorrectionReport.content_fingerprint == fingerprint,
            CorrectionReport.submitted_at >= utcnow() - timedelta(hours=24),
        )
    )
    if duplicate:
        return PublicCorrectionResponse(id=duplicate)
    governed = await db.scalar(
        select(GovernedResource).where(GovernedResource.public_service_id == service_id)
    )
    report = CorrectionReport(
        service_id=service_id,
        published_revision_id=governed.published_revision_id if governed else None,
        category=payload.category,
        description=payload.description,
        reporter_name=payload.reporter_name,
        reporter_email=payload.reporter_email,
        content_fingerprint=fingerprint,
        status=CorrectionStatus.NEW,
    )
    db.add(report)
    await db.flush()
    db.add(
        AuditEvent(
            actor_id=None,
            action="correction.submitted",
            subject_type="correction_report",
            subject_id=str(report.id),
            summary=f"Public correction submitted for category {payload.category.value}",
        )
    )
    await db.commit()
    return PublicCorrectionResponse(id=report.id)


async def _load(
    db: AsyncSession, correction_id: uuid.UUID, *, for_update: bool = False
) -> CorrectionReport:
    statement = select(CorrectionReport).where(CorrectionReport.id == correction_id)
    if for_update:
        statement = statement.with_for_update()
    report = await db.scalar(statement)
    if not report:
        raise HTTPException(404, "Correction report not found")
    return report


@admin_router.get("", response_model=list[CorrectionView])
async def list_corrections(
    db: Database,
    auth: Annotated[AuthContext, Depends(require(Permission.CORRECTION_VIEW))],
    status: CorrectionStatus | None = None,
    resource_id: uuid.UUID | None = None,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[CorrectionView]:
    statement = select(CorrectionReport).order_by(CorrectionReport.submitted_at.desc())
    if status:
        statement = statement.where(CorrectionReport.status == status)
    if resource_id:
        statement = statement.where(CorrectionReport.service_id == resource_id)
    if search:
        statement = statement.where(CorrectionReport.description.ilike(f"%{search[:100]}%"))
    reports = (await db.scalars(statement.offset(max(offset, 0)).limit(min(limit, 100)))).all()
    show_contact = Permission.CORRECTION_VIEW_CONTACT in permissions_for(auth.account)
    return [_correction_view(item, show_contact=show_contact) for item in reports]


@admin_router.get("/{correction_id}", response_model=CorrectionView)
async def get_correction(
    correction_id: uuid.UUID,
    db: Database,
    auth: Annotated[AuthContext, Depends(require(Permission.CORRECTION_VIEW))],
) -> CorrectionView:
    return _correction_view(
        await _load(db, correction_id),
        show_contact=Permission.CORRECTION_VIEW_CONTACT in permissions_for(auth.account),
    )


ACTION_PERMISSION = {
    "claim": Permission.CORRECTION_CLAIM,
    "release": Permission.CORRECTION_CLAIM,
    "assign": Permission.CORRECTION_ASSIGN,
    "triage": Permission.CORRECTION_TRIAGE,
    "duplicate": Permission.CORRECTION_MARK_DUPLICATE,
    "abuse": Permission.CORRECTION_MARK_ABUSE,
    "dismiss": Permission.CORRECTION_DISMISS,
    "escalate": Permission.CORRECTION_REQUEST_REVERIFICATION,
    "resolve": Permission.CORRECTION_RESOLVE,
    "reopen": Permission.CORRECTION_REOPEN,
}


@admin_router.post("/{correction_id}/{action}", response_model=CorrectionView)
async def act_on_correction(
    correction_id: uuid.UUID,
    action: str,
    payload: CorrectionAction,
    db: Database,
    csrf: CsrfAuth,
) -> CorrectionView:
    permission = ACTION_PERMISSION.get(action)
    if not permission or permission not in permissions_for(csrf.account):
        raise HTTPException(403, "Permission denied")
    report = await _load(db, correction_id, for_update=True)
    if report.version != payload.expected_version:
        raise HTTPException(409, "Correction changed; reload before continuing")
    terminal = {
        CorrectionStatus.DUPLICATE,
        CorrectionStatus.RESOLVED,
        CorrectionStatus.DISMISSED,
        CorrectionStatus.ABUSE,
    }
    if report.status in terminal and action != "reopen":
        raise HTTPException(409, "Correction is already closed")
    if action == "claim":
        if report.assigned_reviewer_id and report.assigned_reviewer_id != csrf.account.id:
            raise HTTPException(409, "Correction is already assigned")
        report.assigned_reviewer_id = csrf.account.id
    elif action == "assign":
        if not payload.assignee_id:
            raise HTTPException(422, "An assignee is required")
        report.assigned_reviewer_id = payload.assignee_id
    elif action == "release":
        report.assigned_reviewer_id = None
    elif action == "triage":
        report.status = CorrectionStatus.TRIAGED
    elif action == "duplicate":
        if not payload.duplicate_of_id or payload.duplicate_of_id == report.id:
            raise HTTPException(422, "A different correction is required")
        report.duplicate_of_id = payload.duplicate_of_id
        report.status = CorrectionStatus.DUPLICATE
        report.resolution_reason = payload.reason or "Duplicate report"
        report.resolved_at = utcnow()
    elif action in {"abuse", "dismiss", "resolve"}:
        if not payload.reason:
            raise HTTPException(422, "A reason is required")
        report.status = {
            "abuse": CorrectionStatus.ABUSE,
            "dismiss": CorrectionStatus.DISMISSED,
            "resolve": CorrectionStatus.RESOLVED,
        }[action]
        report.resolution_reason = payload.reason
        report.resolved_at = utcnow()
    elif action == "reopen":
        report.status = CorrectionStatus.TRIAGED
        report.resolution_reason = None
        report.resolved_at = None
    elif action == "escalate":
        task = None
        if payload.task_id:
            task = await db.get(ReverificationTask, payload.task_id)
            if not task or task.service_id != report.service_id or not task.active:
                raise HTTPException(422, "Active re-verification task is invalid")
        if not task:
            task = await db.scalar(
                select(ReverificationTask).where(
                    ReverificationTask.service_id == report.service_id,
                    ReverificationTask.active.is_(True),
                )
            )
        if not task:
            governed = await db.scalar(
                select(GovernedResource).where(
                    GovernedResource.public_service_id == report.service_id
                )
            )
            task = ReverificationTask(
                service_id=report.service_id,
                resource_id=governed.id if governed else None,
                published_revision_id=governed.published_revision_id if governed else None,
                trigger_source="public_correction",
                reason=f"correction:{report.category.value}",
                freshness_state="reported_change",
                due_at=utcnow() + timedelta(days=7),
                status=ReverificationStatus.OPEN,
                active=True,
            )
            db.add(task)
            await db.flush()
        report.task_id = task.id
        report.status = CorrectionStatus.NEEDS_REVERIFICATION
    report.version += 1
    db.add(
        AuditEvent(
            actor_id=csrf.account.id,
            action=f"correction.{action}",
            subject_type="correction_report",
            subject_id=str(report.id),
            summary=f"Correction action completed: {action}",
        )
    )
    await db.commit()
    await db.refresh(report)
    return _correction_view(
        report, show_contact=Permission.CORRECTION_VIEW_CONTACT in permissions_for(csrf.account)
    )
