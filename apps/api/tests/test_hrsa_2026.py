import csv
import json
from pathlib import Path

import pytest

from civicsignal_api.services.hrsa_2026 import prepare_hrsa_2026_snapshot


def _write_fixture(path: Path) -> None:
    headers = [
        "Health Center Type",
        "Health Center Number",
        "BPHC Assigned Number",
        "Site Name",
        "Site Address",
        "Site City",
        "Site State Abbreviation",
        "Site Postal Code",
        "Site Telephone Number",
        "Site Web Address",
        "Operating Hours per Week",
        "Site Status Description",
        "Health Center Name",
        "Complete County Name",
        "Data Warehouse Record Create Date",
    ]
    rows = [
        [
            "FQHC",
            "H80CS00001",
            "BPS-001",
            "Example Health Center",
            "1 Main St",
            "Boston",
            "MA",
            "02108",
            "617-555-0100",
            "health.example",
            "40",
            "Active",
            "Example Health Organization",
            "Suffolk County",
            "07/17/2026",
        ],
        [
            "FQHC",
            "H80CS00002",
            "BPS-002",
            "Old Center",
            "2 Main St",
            "Boston",
            "MA",
            "02108",
            "617-555-0101",
            "old.example",
            "20",
            "Active",
            "Example Health Organization",
            "Suffolk County",
            "12/31/2025",
        ],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def test_prepares_only_active_2026_candidates_in_bounded_chunks(tmp_path: Path) -> None:
    source = tmp_path / "hrsa.csv"
    output = tmp_path / "staged"
    _write_fixture(source)
    summary = prepare_hrsa_2026_snapshot(
        source,
        output,
        source_updated_at="2026-07-18",
        retrieved_at="2026-07-18T21:30:00Z",
    )
    assert summary.raw_rows == 2
    assert summary.staged_rows == 1
    assert summary.skipped_non_2026 == 1
    manifest = json.loads((output / "manifest.json").read_text())
    candidate = json.loads((output / manifest["chunks"][0]["filename"]).read_text())[0]
    assert candidate["source_identifier"] == "BPS-001"
    assert candidate["region"] == "MA"
    assert candidate["website"] == "https://health.example/"
    assert manifest["publication_status"].startswith("blocked_pending")


def test_rejects_a_snapshot_without_required_columns_or_2026_update(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("name\nexample\n")
    with pytest.raises(ValueError, match="must be in 2026"):
        prepare_hrsa_2026_snapshot(
            source,
            tmp_path / "out",
            source_updated_at="2025-12-31",
            retrieved_at="2026-07-18T21:30:00Z",
        )
    with pytest.raises(ValueError, match="missing columns"):
        prepare_hrsa_2026_snapshot(
            source,
            tmp_path / "out",
            source_updated_at="2026-07-18",
            retrieved_at="2026-07-18T21:30:00Z",
        )
