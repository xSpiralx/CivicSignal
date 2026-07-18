from sqlalchemy import select

from civicsignal_api.models.auth import AdminAccount, AuditEvent, Role, RoleName
from civicsignal_api.security import hash_password


async def create_account(app) -> None:  # type: ignore[no-untyped-def]
    async with app.state.session_factory() as db:
        role = Role(id=5, name=RoleName.ADMINISTRATOR)
        account = AdminAccount(
            email="admin@example.test",
            display_name="Test Administrator",
            password_hash=hash_password("correct horse battery staple"),
            roles=[role],
        )
        db.add(account)
        await db.commit()


async def test_sign_in_session_csrf_and_sign_out(app, client) -> None:  # type: ignore[no-untyped-def]
    await create_account(app)
    response = await client.post(
        "/api/v1/admin/auth/sign-in",
        json={"email": " ADMIN@example.test ", "password": "correct horse battery staple"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["account"]["roles"] == ["administrator"]
    assert "admin.manage" in body["account"]["permissions"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]

    current = await client.get("/api/v1/admin/auth/session")
    assert current.status_code == 200
    current_csrf = current.json()["csrf_token"]
    audit = await client.get("/api/v1/admin/audit")
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "auth.sign_in"
    assert "token" not in audit.text.lower()

    rejected = await client.post("/api/v1/admin/auth/sign-out")
    assert rejected.status_code == 403
    signed_out = await client.post(
        "/api/v1/admin/auth/sign-out", headers={"X-CSRF-Token": current_csrf}
    )
    assert signed_out.status_code == 204
    assert (await client.get("/api/v1/admin/auth/session")).status_code == 401

    async with app.state.session_factory() as db:
        actions = list(await db.scalars(select(AuditEvent.action).order_by(AuditEvent.created_at)))
    assert actions == ["auth.sign_in", "auth.sign_out"]


async def test_sign_in_uses_generic_failure_and_cooldown(app, client) -> None:  # type: ignore[no-untyped-def]
    await create_account(app)
    unknown = await client.post(
        "/api/v1/admin/auth/sign-in",
        json={"email": "unknown@example.test", "password": "incorrect password"},
    )
    wrong = None
    for _ in range(5):
        wrong = await client.post(
            "/api/v1/admin/auth/sign-in",
            json={"email": "admin@example.test", "password": "incorrect password"},
        )
    assert wrong is not None
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["error"]["message"] == wrong.json()["error"]["message"]
    blocked = await client.post(
        "/api/v1/admin/auth/sign-in",
        json={"email": "admin@example.test", "password": "correct horse battery staple"},
    )
    assert blocked.status_code == 401
