from datetime import timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from civicsignal_api.models.auth import AdminAccount, Role, RoleName
from civicsignal_api.schemas.governance import DraftContent
from civicsignal_api.security import hash_password, utcnow

CONTENT = {
    "organization_name": "Example Community Network",
    "organization_description": "Fictional provider for automated testing.",
    "organization_type": "nonprofit",
    "service_name": "Example support line",
    "description": "Fictional information and referral support.",
    "eligibility": "Residents of Example County",
    "languages": ["English"],
    "accessibility": "Relay calls supported",
    "emergency_availability": False,
    "source_name": "Provider service page",
    "source_url": "https://provider.example/services/support",
    "source_organization": "Example Community Network",
}


def test_geography_normalizes_state_and_rejects_unknown_timezone() -> None:
    content = DraftContent.model_validate({**CONTENT, "region": "massachusetts", "country": "us"})
    assert content.region == "MA" and content.country == "US"
    with pytest.raises(ValidationError, match="valid IANA time zone"):
        DraftContent.model_validate({**CONTENT, "timezone": "America/Imaginary"})


async def login_admin(app: Any, client: Any) -> str:
    async with app.state.session_factory() as db:
        roles = [Role(id=index, name=name) for index, name in enumerate(RoleName, 1)]
        db.add_all(roles)
        db.add(
            AdminAccount(
                email="governance@example.test",
                display_name="Governance Admin",
                password_hash=hash_password("correct horse battery staple"),
                roles=[roles[-1]],
            )
        )
        await db.commit()
    response = await client.post(
        "/api/v1/admin/auth/sign-in",
        json={"email": "governance@example.test", "password": "correct horse battery staple"},
    )
    return str(response.json()["csrf_token"])


async def act(
    client: Any, csrf: str, resource_id: str, action: str, revision: int, **extra: Any
) -> Any:
    return await client.post(
        f"/api/v1/admin/resources/{resource_id}/{action}",
        headers={"X-CSRF-Token": csrf},
        json={"expected_revision": revision, **extra},
    )


async def test_versioned_lifecycle_and_publication(app, client) -> None:  # type: ignore[no-untyped-def]
    csrf = await login_admin(app, client)
    created = await client.post(
        "/api/v1/admin/resources", headers={"X-CSRF-Token": csrf}, json={"content": CONTENT}
    )
    assert created.status_code == 201
    resource = created.json()
    resource_id = resource["id"]
    updated_content = {
        **CONTENT,
        "description": "Updated fictional referral support.",
        "city": "Boston",
        "region": "Massachusetts",
        "postal_code": "02108",
        "timezone": "America/New_York",
    }
    updated = await client.put(
        f"/api/v1/admin/resources/{resource_id}",
        headers={"X-CSRF-Token": csrf},
        json={"expected_revision": 1, "content": updated_content},
    )
    assert updated.status_code == 200 and updated.json()["revision"] == 2
    stale = await client.put(
        f"/api/v1/admin/resources/{resource_id}",
        headers={"X-CSRF-Token": csrf},
        json={"expected_revision": 1, "content": CONTENT},
    )
    assert stale.status_code == 409
    assert (await act(client, csrf, resource_id, "submit", 2)).json()["state"] == "submitted"
    assert (await act(client, csrf, resource_id, "advance", 2)).json()[
        "state"
    ] == "pending_verification"
    due = (utcnow() + timedelta(days=90)).isoformat()
    verified = await act(
        client,
        csrf,
        resource_id,
        "verify",
        2,
        evidence=["https://provider.example/services/support"],
        next_due_at=due,
    )
    assert verified.json()["state"] == "verified"
    published = await act(client, csrf, resource_id, "publish", 2)
    assert published.status_code == 200 and published.json()["state"] == "published"
    service_id = published.json()["public_service_id"]
    public = await client.get(f"/api/v1/services/{service_id}")
    assert public.status_code == 200
    assert public.json()["name"] == "Example support line"
    assert public.json()["locations"][0]["region"] == "MA"
    assert public.json()["locations"][0]["timezone"] == "America/New_York"


async def test_invalid_transition_and_required_reason(app, client) -> None:  # type: ignore[no-untyped-def]
    csrf = await login_admin(app, client)
    created = await client.post(
        "/api/v1/admin/resources", headers={"X-CSRF-Token": csrf}, json={"content": CONTENT}
    )
    resource_id = created.json()["id"]
    assert (await act(client, csrf, resource_id, "publish", 1)).status_code == 409
    await act(client, csrf, resource_id, "submit", 1)
    assert (await act(client, csrf, resource_id, "request-changes", 1)).status_code == 422
