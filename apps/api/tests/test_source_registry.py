import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from civicsignal_api.models.auth import AdminAccount, AuditEvent, Role, RoleName
from civicsignal_api.models.governance import GovernedResource, WorkflowState
from civicsignal_api.models.ingestion import ApprovedSource, CandidateResource, SourceApprovalStatus
from civicsignal_api.security import hash_password
from civicsignal_api.services.ingestion import preview_or_import_file


async def login_admin(app, client) -> str:  # type: ignore[no-untyped-def]
    async with app.state.session_factory() as db:
        role = Role(id=5, name=RoleName.ADMINISTRATOR)
        db.add(
            AdminAccount(
                email="sources@example.test",
                display_name="Source Reviewer",
                password_hash=hash_password("correct horse battery staple"),
                roles=[role],
            )
        )
        await db.commit()
    response = await client.post(
        "/api/v1/admin/auth/sign-in",
        json={"email": "sources@example.test", "password": "correct horse battery staple"},
    )
    return str(response.json()["csrf_token"])


async def test_source_requires_governed_decision_before_automation(app, client) -> None:  # type: ignore[no-untyped-def]
    csrf = await login_admin(app, client)
    proposed = await client.post(
        "/api/v1/admin/sources",
        headers={"X-CSRF-Token": csrf},
        json={
            "stable_identifier": "example-open-data",
            "name": "Example open data",
            "publishing_organization": "Example government",
            "source_url": "https://data.example.gov/resources.json",
            "source_type": "government_open_data",
            "geographic_scope": "United States",
            "resource_categories": ["food assistance"],
            "automation_permission": True,
            "allowed_hosts": ["data.example.gov"],
        },
    )
    assert proposed.status_code == 201
    assert proposed.json()["approval_status"] == "proposed"
    assert proposed.json()["automation_permission"] is False
    assert proposed.json()["enabled"] is False

    invalid = await client.put(
        f"/api/v1/admin/sources/{proposed.json()['id']}/decision",
        headers={"X-CSRF-Token": csrf},
        json={
            "approval_status": "under_review",
            "reason": "Legal permission is still being evaluated.",
            "enabled": True,
            "automation_permission": True,
            "allowed_hosts": ["data.example.gov"],
            "last_legal_review_at": datetime.now(UTC).isoformat(),
            "last_technical_review_at": datetime.now(UTC).isoformat(),
        },
    )
    assert invalid.status_code == 422

    approved = await client.put(
        f"/api/v1/admin/sources/{proposed.json()['id']}/decision",
        headers={"X-CSRF-Token": csrf},
        json={
            "approval_status": "approved",
            "reason": "Explicit open-data terms permit reuse and automated retrieval.",
            "enabled": True,
            "automation_permission": True,
            "allowed_hosts": ["DATA.EXAMPLE.GOV"],
            "license_name": "Public domain",
            "license_url": "https://data.example.gov/terms",
            "terms_url": "https://data.example.gov/terms",
            "attribution_requirement": "Source: Example government",
            "redistribution_permitted": True,
            "modification_permitted": True,
            "last_legal_review_at": datetime.now(UTC).isoformat(),
            "last_technical_review_at": datetime.now(UTC).isoformat(),
        },
    )
    assert approved.status_code == 200
    assert approved.json()["enabled"] is True
    assert approved.json()["allowed_hosts"] == ["data.example.gov"]
    async with app.state.session_factory() as db:
        source = await db.scalar(select(ApprovedSource))
        actions = list(await db.scalars(select(AuditEvent.action).order_by(AuditEvent.created_at)))
    assert source is not None and source.may_run_automatically
    assert "source.propose" in actions and "source.approved" in actions


async def test_import_dry_run_creates_no_records_and_acceptance_creates_only_draft(
    app: Any, client: Any, tmp_path: Path
) -> None:
    csrf = await login_admin(app, client)
    async with app.state.session_factory() as db:
        actor = await db.scalar(select(AdminAccount))
        assert actor is not None
        source = ApprovedSource(
            stable_identifier="fictional-test-source",
            name="Fictional test source",
            publishing_organization="Example government",
            source_url="https://data.example.gov/resources.json",
            source_type="government_open_data",
            geographic_scope="Example County",
            resource_categories=["food assistance"],
            license_name="Public domain test fixture",
            automation_permission=True,
            redistribution_permitted=True,
            modification_permitted=True,
            allowed_hosts=["data.example.gov"],
            approval_status=SourceApprovalStatus.APPROVED,
            enabled=True,
            reviewer_id=actor.id,
            import_method="controlled_file",
            reliability_classification="test_fixture",
        )
        db.add(source)
        await db.commit()
        fixture = tmp_path / "resources.json"
        fixture.write_text(
            json.dumps(
                [
                    {
                        "source_identifier": "fixture-1",
                        "organization_name": "Example Government",
                        "organization_description": "Fictional test fixture.",
                        "organization_type": "government",
                        "service_name": "Example Support",
                        "description": "Fictional service for import testing.",
                        "city": "Exampleville",
                        "region": "MA",
                        "categories": ["Food"],
                        "source_name": "Example dataset",
                        "source_url": "https://data.example.gov/resources/1",
                        "source_organization": "Example government",
                        "source_record_updated_at": "2026-07-18",
                    }
                ]
            )
        )
        dry_run = await preview_or_import_file(
            db,
            source_identifier=source.stable_identifier,
            actor_id=actor.id,
            file_path=fixture,
            media_type="application/json",
            commit=False,
        )
        assert dry_run.valid == 1 and dry_run.batch_id is None
        assert await db.scalar(select(CandidateResource)) is None
        committed = await preview_or_import_file(
            db,
            source_identifier=source.stable_identifier,
            actor_id=actor.id,
            file_path=fixture,
            media_type="application/json",
            commit=True,
        )
        candidate = await db.scalar(select(CandidateResource))
        actions = list(await db.scalars(select(AuditEvent.action)))
        assert committed.batch_id is not None and candidate is not None
        repeated = await preview_or_import_file(
            db,
            source_identifier=source.stable_identifier,
            actor_id=actor.id,
            file_path=fixture,
            media_type="application/json",
            commit=True,
        )
        assert repeated.batch_id == committed.batch_id
        assert len(list(await db.scalars(select(CandidateResource)))) == 1
        assert "import.batch.create" in actions
        assert await db.scalar(select(GovernedResource)) is None
        candidate_id = candidate.id
    queue = await client.get("/api/v1/admin/imports/candidates?state=MA&city=Exampleville")
    assert queue.status_code == 200
    assert queue.json()["pagination"]["total"] == 1
    assert queue.json()["items"][0]["review_status"] == "ready_for_review"
    accepted = await client.post(
        f"/api/v1/admin/imports/{committed.batch_id}/candidates/{candidate_id}/accept",
        headers={"X-CSRF-Token": csrf},
    )
    assert accepted.status_code == 200
    assert accepted.json()["state"] == WorkflowState.DRAFT.value
    assert accepted.json()["public_service_id"] is None


async def test_import_rejects_old_and_missing_freshness(
    app: Any, client: Any, tmp_path: Path
) -> None:
    async with app.state.session_factory() as db:
        role = Role(id=5, name=RoleName.ADMINISTRATOR)
        actor = AdminAccount(
            email="freshness@example.test",
            display_name="Freshness Reviewer",
            password_hash=hash_password("correct horse battery staple"),
            roles=[role],
        )
        db.add(actor)
        await db.flush()
        source = ApprovedSource(
            stable_identifier="freshness-test-source",
            name="Freshness test source",
            publishing_organization="Example government",
            source_url="https://data.example.gov/resources.json",
            source_type="government_open_data",
            geographic_scope="United States",
            resource_categories=["food"],
            license_name="Public domain fixture",
            redistribution_permitted=True,
            automation_permission=True,
            allowed_hosts=["data.example.gov"],
            approval_status=SourceApprovalStatus.APPROVED,
            enabled=True,
            reviewer_id=actor.id,
        )
        db.add(source)
        await db.commit()
        rows = []
        for identifier, freshness in (("old", "2024-12-31"), ("missing", None)):
            row = {
                "source_identifier": identifier,
                "organization_name": "Example",
                "organization_description": "Fixture",
                "organization_type": "government",
                "service_name": identifier,
                "description": "Fixture",
                "source_name": "Fixture",
                "source_url": "https://data.example.gov/resources",
                "source_organization": "Example government",
            }
            if freshness:
                row["source_record_updated_at"] = freshness
            rows.append(row)
        fixture = tmp_path / "freshness.json"
        fixture.write_text(json.dumps(rows))
        result = await preview_or_import_file(
            db,
            source_identifier=source.stable_identifier,
            actor_id=actor.id,
            file_path=fixture,
            media_type="application/json",
            commit=False,
        )
        assert result.valid == 0
        assert result.rejected == 2
        assert all("2025-2026" in item["error"] for item in result.errors)
