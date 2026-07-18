from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select

from civicsignal_api.models.resource import (
    Category,
    ContactChannel,
    ContactType,
    Location,
    Organization,
    Service,
    Source,
    SourceType,
    Verification,
    VerificationStatus,
)
from civicsignal_api.services.resources import transition_verification


async def add_service(
    app: FastAPI, *, status: VerificationStatus = VerificationStatus.VERIFIED, active: bool = True
) -> Service:
    now = datetime.now(UTC)
    organization = Organization(
        public_name="Test Community Organization",
        description="Test description",
        organization_type="test",
        languages="English, Spanish",
        is_active=True,
    )
    category = Category(
        slug=f"food-{status.value}-{active}", name=f"Food {status.value} {active}", is_active=True
    )
    service = Service(
        organization=organization,
        name="Food Pantry Support",
        description="Provides grocery assistance.",
        eligibility="Residents of Test City",
        languages="English, Spanish",
        accessibility="Wheelchair accessible",
        is_active=active,
        emergency_availability=False,
    )
    service.categories.append(category)
    service.locations.append(
        Location(
            organization=organization,
            display_name="Test Center",
            city="Test City",
            region="TS",
            postal_code="12345",
            country="US",
            timezone="UTC",
            is_active=True,
        )
    )
    service.contacts.append(
        ContactChannel(
            channel_type=ContactType.PHONE, label="Phone", value="555-0100", is_primary=True
        )
    )
    service.sources.append(
        Source(
            name="Test source",
            url="https://source.example",
            organization="Test",
            source_type=SourceType.DEMONSTRATION,
            retrieved_at=now,
            last_checked_at=now,
        )
    )
    service.verifications.append(
        Verification(
            status=status,
            checked_at=now,
            expires_at=now + timedelta(days=30),
            checked_by="test reviewer",
            notes="private review note",
        )
    )
    async with app.state.session_factory() as session:
        session.add(organization)
        await session.commit()
        await session.refresh(service)
    return service


async def test_public_api_filters_and_does_not_leak_notes(
    app: FastAPI, client: AsyncClient
) -> None:
    service = await add_service(app)
    response = await client.get(
        "/api/v1/services",
        params={
            "city": "Test City",
            "language": "Spanish",
            "eligibility": "residents",
            "sort": "state_city",
            "q": "grocery",
        },
    )
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1
    assert response.json()["items"][0]["id"] == str(service.id)
    detail = await client.get(f"/api/v1/services/{service.id}")
    assert detail.status_code == 200
    assert "notes" not in detail.text and "checked_by" not in detail.text


@pytest.mark.parametrize(
    "status", [VerificationStatus.DRAFT, VerificationStatus.REJECTED, VerificationStatus.ARCHIVED]
)
async def test_nonpublic_verification_states_are_hidden(
    app: FastAPI, client: AsyncClient, status: VerificationStatus
) -> None:
    service = await add_service(app, status=status)
    assert (await client.get(f"/api/v1/services/{service.id}")).status_code == 404


async def test_inactive_service_is_hidden(app: FastAPI, client: AsyncClient) -> None:
    service = await add_service(app, active=False)
    assert (await client.get(f"/api/v1/services/{service.id}")).status_code == 404


async def test_pagination_and_invalid_input(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/services", params={"page_size": 51})).status_code == 422
    assert (await client.get("/api/v1/services", params={"q": "x" * 201})).status_code == 422
    assert (await client.get("/api/v1/services", params={"sort": "distance"})).status_code == 422
    response = await client.get("/api/v1/services", params={"category": "unsupported"})
    assert response.status_code == 200 and response.json()["items"] == []


async def test_transition_rules(app: FastAPI, client: AsyncClient) -> None:
    service = await add_service(app, status=VerificationStatus.DRAFT)
    async with app.state.session_factory() as session:
        verification = await session.scalar(
            select(Verification).where(Verification.service_id == service.id)
        )
        assert verification
        await transition_verification(session, verification, VerificationStatus.PENDING_REVIEW)
        with pytest.raises(ValueError):
            await transition_verification(session, verification, VerificationStatus.ARCHIVED)
