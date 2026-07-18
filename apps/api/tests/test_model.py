from typing import cast

from sqlalchemy import Enum, Table
from sqlalchemy.schema import CreateTable

from civicsignal_api.models.auth import Role
from civicsignal_api.models.system_record import SystemRecord


def test_system_record_has_expected_table() -> None:
    statement = str(CreateTable(cast(Table, SystemRecord.__table__)).compile())
    assert "system_records" in statement
    assert "created_at" in statement


def test_role_enum_matches_lowercase_migration_values() -> None:
    assert cast(Enum, Role.__table__.c.name.type).enums == [
        "viewer",
        "contributor",
        "reviewer",
        "verifier",
        "administrator",
    ]
