from typing import Any

from civicsignal_api.models.auth import AdminAccount, Role, RoleName
from civicsignal_api.security import hash_password


async def authenticate(app: Any, client: Any) -> str:
    async with app.state.session_factory() as db:
        roles = [Role(id=index, name=name) for index, name in enumerate(RoleName, 1)]
        db.add(
            AdminAccount(
                email="owner@example.test",
                display_name="Owner",
                password_hash=hash_password("correct horse battery staple"),
                roles=[roles[-1]],
            )
        )
        db.add_all(roles[:-1])
        await db.commit()
    signed_in = await client.post(
        "/api/v1/admin/auth/sign-in",
        json={"email": "owner@example.test", "password": "correct horse battery staple"},
    )
    return str(signed_in.json()["csrf_token"])


async def test_account_create_update_sessions_and_last_admin(app, client) -> None:  # type: ignore[no-untyped-def]
    csrf = await authenticate(app, client)
    missing_csrf = await client.post("/api/v1/admin/accounts", json={})
    assert missing_csrf.status_code == 403
    created = await client.post(
        "/api/v1/admin/accounts",
        headers={"X-CSRF-Token": csrf},
        json={
            "email": "reviewer@example.test",
            "display_name": "Reviewer",
            "password": "another correct horse password",
            "roles": ["reviewer"],
        },
    )
    assert created.status_code == 201
    account_id = created.json()["id"]
    duplicate = await client.post(
        "/api/v1/admin/accounts",
        headers={"X-CSRF-Token": csrf},
        json={
            "email": "REVIEWER@example.test",
            "display_name": "Duplicate",
            "password": "another correct horse password",
            "roles": ["viewer"],
        },
    )
    assert duplicate.status_code == 409
    listed = await client.get("/api/v1/admin/accounts")
    assert {item["email"] for item in listed.json()} == {
        "owner@example.test",
        "reviewer@example.test",
    }
    updated = await client.patch(
        f"/api/v1/admin/accounts/{account_id}",
        headers={"X-CSRF-Token": csrf},
        json={"roles": ["verifier"], "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["roles"] == ["verifier"]
    owner_id = next(item["id"] for item in listed.json() if item["email"] == "owner@example.test")
    protected = await client.patch(
        f"/api/v1/admin/accounts/{owner_id}",
        headers={"X-CSRF-Token": csrf},
        json={"is_active": False},
    )
    assert protected.status_code == 409


async def test_password_replacement_revokes_target_sessions(app, client) -> None:  # type: ignore[no-untyped-def]
    csrf = await authenticate(app, client)
    current = await client.get("/api/v1/admin/auth/session")
    csrf = current.json()["csrf_token"]
    owner_id = current.json()["account"]["id"]
    replaced = await client.post(
        f"/api/v1/admin/accounts/{owner_id}/password",
        headers={"X-CSRF-Token": csrf},
        json={"password": "replacement password with length"},
    )
    assert replaced.status_code == 204
    assert (await client.get("/api/v1/admin/auth/session")).status_code == 401
