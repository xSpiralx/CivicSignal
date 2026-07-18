import pytest
from pydantic import ValidationError

from civicsignal_api.core.config import Settings


def test_render_postgres_url_uses_async_driver() -> None:
    settings = Settings(database_url="postgresql://user:secret@private-db:5432/civicsignal")
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_neon_database_url_is_normalized_for_asyncpg() -> None:
    settings = Settings(
        database_url=(
            "postgresql://user:password@db.example/neondb?sslmode=require&channel_binding=require"
        )
    )
    assert settings.database_url == (
        "postgresql+asyncpg://user:password@db.example/neondb?ssl=require"
    )


def test_allowed_hosts_are_explicit() -> None:
    settings = Settings(allowed_hosts="api.internal.example,localhost")
    assert settings.trusted_hosts == ["api.internal.example", "localhost"]


def test_production_fails_closed_without_unique_operational_secrets() -> None:
    with pytest.raises(ValidationError, match="proxy shared secret"):
        Settings(environment="production")
    settings = Settings(
        environment="production",
        proxy_shared_secret="proxy-secret-that-is-longer-than-thirty-two-characters",
        maintenance_token="different-maintenance-secret-longer-than-thirty-two",
    )
    assert settings.demo_mode is False


async def test_configured_api_rejects_requests_outside_controlled_proxy(app, client) -> None:  # type: ignore[no-untyped-def]
    app.state.settings.proxy_shared_secret = "local-test-shared-secret"
    assert (await client.get("/api/v1/categories")).status_code == 403
    allowed = await client.get(
        "/api/v1/categories",
        headers={"X-CivicSignal-Proxy": "local-test-shared-secret"},
    )
    assert allowed.status_code == 200
