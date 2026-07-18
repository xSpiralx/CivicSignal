from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import CorrectionReport, ReverificationTask
from civicsignal_api.models.resource import Verification
from tests.test_governance import CONTENT, act, login_admin
from tests.test_resources import add_service


async def test_public_correction_is_safe_and_deduplicated(app, client) -> None:  # type: ignore[no-untyped-def]
    service = await add_service(app)
    payload = {
        "category": "incorrect_hours",
        "description": "The posted Saturday hours appear to be incorrect.",
        "reporter_name": "Example Visitor",
        "reporter_email": "VISITOR@EXAMPLE.TEST",
    }
    first = await client.post(f"/api/v1/services/{service.id}/corrections", json=payload)
    second = await client.post(f"/api/v1/services/{service.id}/corrections", json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert "public information has not changed" in first.json()["message"].lower()
    async with app.state.session_factory() as db:
        assert await db.scalar(select(func.count(CorrectionReport.id))) == 1
        report = await db.scalar(select(CorrectionReport))
        assert report and report.reporter_email == "visitor@example.test"
        assert await db.scalar(select(func.count(AuditEvent.id))) == 1
        assert await db.scalar(select(func.count(Verification.id))) == 1


async def test_correction_escalation_reuses_task_and_reverification_completes(app, client) -> None:  # type: ignore[no-untyped-def]
    service = await add_service(app)
    for description in (
        "The weekday opening hours appear to have changed.",
        "Please verify the listed closing time with the provider.",
    ):
        response = await client.post(
            f"/api/v1/services/{service.id}/corrections",
            json={"category": "incorrect_hours", "description": description},
        )
        assert response.status_code == 202
    csrf = await login_admin(app, client)
    reports = (await client.get("/api/v1/admin/corrections")).json()
    assert len(reports) == 2 and reports[0]["reporter_email"] is None
    task_ids = []
    for report in reports:
        claimed = await client.post(
            f"/api/v1/admin/corrections/{report['id']}/claim",
            headers={"X-CSRF-Token": csrf},
            json={"expected_version": report["version"]},
        )
        escalated = await client.post(
            f"/api/v1/admin/corrections/{report['id']}/escalate",
            headers={"X-CSRF-Token": csrf},
            json={"expected_version": claimed.json()["version"]},
        )
        assert escalated.status_code == 200
        task_ids.append(escalated.json()["task_id"])
    assert len(set(task_ids)) == 1
    task = (await client.get(f"/api/v1/admin/reverification/{task_ids[0]}")).json()
    claimed_task = await client.post(
        f"/api/v1/admin/reverification/{task['id']}/claim",
        headers={"X-CSRF-Token": csrf},
        json={"expected_version": task["version"]},
    )
    completed = await client.post(
        f"/api/v1/admin/reverification/{task['id']}/confirmed-unchanged",
        headers={"X-CSRF-Token": csrf},
        json={
            "expected_version": claimed_task.json()["version"],
            "evidence_summary": "Provider source and direct contact confirmed the current hours.",
            "source_references": ["https://source.example"],
            "next_due_at": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    resolved = (await client.get("/api/v1/admin/corrections?status=resolved")).json()
    assert len(resolved) == 2
    async with app.state.session_factory() as db:
        assert await db.scalar(select(func.count(ReverificationTask.id))) == 1
        assert await db.scalar(select(func.count(Verification.id))) == 2


async def test_updated_confirmation_publishes_new_revision(app, client) -> None:  # type: ignore[no-untyped-def]
    csrf = await login_admin(app, client)
    created = await client.post(
        "/api/v1/admin/resources",
        headers={"X-CSRF-Token": csrf},
        json={"content": {**CONTENT, "hours": "Monday–Friday, 9:00–17:00"}},
    )
    resource_id = created.json()["id"]
    await act(client, csrf, resource_id, "submit", 1)
    await act(client, csrf, resource_id, "advance", 1)
    due = (datetime.now(UTC) + timedelta(days=90)).isoformat()
    await act(
        client,
        csrf,
        resource_id,
        "verify",
        1,
        evidence=["https://provider.example/services/support"],
        next_due_at=due,
    )
    published = await act(client, csrf, resource_id, "publish", 1)
    service_id = published.json()["public_service_id"]
    correction = await client.post(
        f"/api/v1/services/{service_id}/corrections",
        json={
            "category": "incorrect_hours",
            "description": "The provider now closes at six in the evening.",
        },
    )
    report_id = correction.json()["id"]
    escalated = await client.post(
        f"/api/v1/admin/corrections/{report_id}/escalate",
        headers={"X-CSRF-Token": csrf},
        json={"expected_version": 1},
    )
    task_id = escalated.json()["task_id"]
    updated = await client.post(
        f"/api/v1/admin/reverification/{task_id}/updated-confirmed",
        headers={"X-CSRF-Token": csrf},
        json={
            "expected_version": 1,
            "expected_revision": 1,
            "evidence_summary": "Provider source confirms the new closing time.",
            "source_references": ["https://provider.example/services/support"],
            "next_due_at": due,
            "proposed_content": {**CONTENT, "hours": "Monday–Friday, 9:00–18:00"},
        },
    )
    assert updated.status_code == 200, updated.text
    governed = await client.get(f"/api/v1/admin/resources/{resource_id}")
    assert governed.json()["revision"] == 2
    public = await client.get(f"/api/v1/services/{service_id}")
    assert public.json()["locations"][0]["hours"] == "Monday–Friday, 9:00–18:00"


async def test_correction_validation_and_rate_limit(app, client) -> None:  # type: ignore[no-untyped-def]
    service = await add_service(app)
    invalid_email = await client.post(
        f"/api/v1/services/{service.id}/corrections",
        json={
            "category": "other",
            "description": "A sufficiently detailed report.",
            "reporter_email": "invalid",
        },
    )
    honeypot = await client.post(
        f"/api/v1/services/{service.id}/corrections",
        json={
            "category": "other",
            "description": "A sufficiently detailed report.",
            "website": "spam",
        },
    )
    assert invalid_email.status_code == honeypot.status_code == 422
    statuses = []
    for index in range(10):
        response = await client.post(
            f"/api/v1/services/{service.id}/corrections",
            json={
                "category": "other",
                "description": f"Unique bounded correction report number {index}.",
            },
        )
        statuses.append(response.status_code)
    assert 429 in statuses
