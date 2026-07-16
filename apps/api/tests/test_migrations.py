from pathlib import Path

from pytest import MonkeyPatch

from alembic import command
from alembic.config import Config
from civicsignal_api.core.config import get_settings


def test_migrations_upgrade_and_downgrade(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    database = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database}")
    get_settings.cache_clear()
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    command.downgrade(config, "20260716_0001")
    command.upgrade(config, "head")
    get_settings.cache_clear()
