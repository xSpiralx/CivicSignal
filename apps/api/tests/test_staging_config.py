from civicsignal_api.core.config import Settings


def test_render_postgres_url_uses_async_driver() -> None:
    settings = Settings(database_url="postgresql://user:secret@private-db:5432/civicsignal")
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_allowed_hosts_are_explicit() -> None:
    settings = Settings(allowed_hosts="api.internal.example,localhost")
    assert settings.trusted_hosts == ["api.internal.example", "localhost"]
