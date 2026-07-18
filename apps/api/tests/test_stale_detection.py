from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from sqlalchemy import func, select

from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import ReverificationTask
from civicsignal_api.models.resource import Verification, VerificationStatus
from civicsignal_api.services.stale_detection import detect_stale, freshness_at
from tests.test_resources import add_service


def test_freshness_boundaries_are_deterministic() -> None:
    now = datetime(2026, 7, 16, tzinfo=UTC)
    assert freshness_at(now + timedelta(days=15), now) == "current"
    assert freshness_at(now + timedelta(days=14), now) == "due_soon"
    assert freshness_at(now, now) == "due"
    assert freshness_at(now - timedelta(days=8), now) == "overdue"
    assert freshness_at(now - timedelta(days=31), now) == "critically_stale"


async def test_detection_is_idempotent_and_dry_run_is_read_only(
    app: FastAPI, client: object
) -> None:
    service = await add_service(app)
    now = datetime.now(UTC)
    async with app.state.session_factory() as db:
        verification = await db.scalar(
            select(Verification).where(Verification.service_id == service.id)
        )
        assert verification
        verification.expires_at = now - timedelta(days=10)
        await db.commit()

        preview = await detect_stale(db, now=now, dry_run=True)
        assert preview.overdue == 1 and preview.tasks_created == 1
        assert await db.scalar(select(func.count(ReverificationTask.id))) == 0

        first = await detect_stale(db, now=now)
        second = await detect_stale(db, now=now)
        assert first.tasks_created == 1 and first.resources_transitioned == 1
        assert second.tasks_created == 0 and second.tasks_existing == 1
        assert await db.scalar(select(func.count(ReverificationTask.id))) == 1
        assert await db.scalar(select(func.count(AuditEvent.id))) == 1
        await db.refresh(verification)
        assert verification.status == VerificationStatus.NEEDS_REVERIFICATION
