from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import (
    GovernedResource,
    ReverificationTask,
    WorkflowState,
)
from civicsignal_api.models.resource import Service, Verification, VerificationStatus

Freshness = Literal["current", "due_soon", "due", "overdue", "critically_stale", "unknown"]


@dataclass
class StaleDetectionSummary:
    examined: int = 0
    current: int = 0
    due_soon: int = 0
    due: int = 0
    overdue: int = 0
    critically_stale: int = 0
    unknown: int = 0
    tasks_created: int = 0
    tasks_existing: int = 0
    resources_transitioned: int = 0
    dry_run: bool = False

    def as_dict(self) -> dict[str, int | bool]:
        return asdict(self)


def freshness_at(expires_at: datetime | None, now: datetime) -> Freshness:
    if expires_at is None:
        return "unknown"
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    days = (expires_at - now).total_seconds() / 86_400
    if days < -30:
        return "critically_stale"
    if days < -7:
        return "overdue"
    if days <= 0:
        return "due"
    if days <= 14:
        return "due_soon"
    return "current"


async def detect_stale(
    db: AsyncSession, *, now: datetime | None = None, dry_run: bool = False
) -> StaleDetectionSummary:
    execution_time = now or datetime.now(UTC)
    if execution_time.tzinfo is None:
        execution_time = execution_time.replace(tzinfo=UTC)
    summary = StaleDetectionSummary(dry_run=dry_run)

    if db.bind and db.bind.dialect.name == "postgresql":
        locked = await db.scalar(text("SELECT pg_try_advisory_xact_lock(1129467207)"))
        if not locked:
            raise RuntimeError("stale detection is already running")

    latest = (
        select(Verification.service_id, func.max(Verification.checked_at).label("checked_at"))
        .group_by(Verification.service_id)
        .subquery()
    )
    records = (
        await db.execute(
            select(Service, Verification, GovernedResource)
            .join(latest, latest.c.service_id == Service.id)
            .join(
                Verification,
                (Verification.service_id == latest.c.service_id)
                & (Verification.checked_at == latest.c.checked_at),
            )
            .outerjoin(GovernedResource, GovernedResource.public_service_id == Service.id)
            .where(
                Service.is_active.is_(True),
                Verification.status.in_(
                    (VerificationStatus.VERIFIED, VerificationStatus.NEEDS_REVERIFICATION)
                ),
            )
        )
    ).all()

    for service, verification, governed in records:
        state = freshness_at(verification.expires_at, execution_time)
        summary.examined += 1
        setattr(summary, state, getattr(summary, state) + 1)
        if state not in ("due", "overdue", "critically_stale"):
            continue
        existing = await db.scalar(
            select(ReverificationTask.id).where(
                ReverificationTask.service_id == service.id,
                ReverificationTask.active.is_(True),
            )
        )
        if existing:
            summary.tasks_existing += 1
            continue
        summary.tasks_created += 1
        if dry_run:
            continue
        db.add(
            ReverificationTask(
                service_id=service.id,
                resource_id=governed.id if governed else None,
                reason="freshness_policy_due",
                freshness_state=state,
                due_at=verification.expires_at,
            )
        )
        if verification.status != VerificationStatus.NEEDS_REVERIFICATION:
            verification.status = VerificationStatus.NEEDS_REVERIFICATION
            summary.resources_transitioned += 1
        if governed and governed.state == WorkflowState.PUBLISHED:
            governed.state = WorkflowState.NEEDS_REVERIFICATION
        db.add(
            AuditEvent(
                actor_id=None,
                action="resource.stale_detected",
                subject_type="service",
                subject_id=str(service.id),
                summary=f"Freshness transitioned to {state}; re-verification queued",
            )
        )
    if dry_run:
        await db.rollback()
    else:
        await db.commit()
    return summary
