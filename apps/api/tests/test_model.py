from typing import cast

from sqlalchemy import Table
from sqlalchemy.schema import CreateTable

from civicsignal_api.models.system_record import SystemRecord


def test_system_record_has_expected_table() -> None:
    statement = str(CreateTable(cast(Table, SystemRecord.__table__)).compile())
    assert "system_records" in statement
    assert "created_at" in statement
