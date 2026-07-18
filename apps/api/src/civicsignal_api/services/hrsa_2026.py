import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import HttpUrl, TypeAdapter, ValidationError

HRSA_SOURCE_IDENTIFIER = "hrsa-health-center-sites-2026"
HRSA_SOURCE_URL = "https://data.hrsa.gov/data/download?titleFilter=Health+Center"
MAX_CHUNK_BYTES = 900_000
MAX_CHUNK_ROWS = 500
REQUIRED_COLUMNS = {
    "BPHC Assigned Number",
    "Complete County Name",
    "Data Warehouse Record Create Date",
    "Health Center Name",
    "Health Center Number",
    "Health Center Type",
    "Operating Hours per Week",
    "Site Address",
    "Site City",
    "Site Name",
    "Site Postal Code",
    "Site State Abbreviation",
    "Site Status Description",
    "Site Telephone Number",
    "Site Web Address",
}
HTTP_URL = TypeAdapter(HttpUrl)


@dataclass(frozen=True)
class StagingSummary:
    raw_rows: int
    staged_rows: int
    skipped_non_2026: int
    skipped_inactive: int
    rejected_rows: int
    chunks: int
    source_sha256: str
    manifest_path: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _clean(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def _website(value: str | None) -> str | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    if " " in cleaned:
        return None
    if "://" not in cleaned:
        cleaned = f"https://{cleaned}"
    try:
        return str(HTTP_URL.validate_python(cleaned))
    except ValidationError:
        return None


def _record_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value.strip(), "%m/%d/%Y")
    except ValueError:
        return None


def _candidate(row: dict[str, str], retrieved_at: str) -> dict[str, Any] | None:
    identifier = _clean(row.get("BPHC Assigned Number")) or _clean(row.get("Health Center Number"))
    site_name = _clean(row.get("Site Name"))
    organization = _clean(row.get("Health Center Name"))
    region = _clean(row.get("Site State Abbreviation")).upper()
    if not all((identifier, site_name, organization, region)):
        return None
    hours = _clean(row.get("Operating Hours per Week"))
    source_record_date = _clean(row.get("Data Warehouse Record Create Date"))
    return {
        "source_identifier": identifier,
        "organization_name": organization,
        "organization_description": (
            "Organization listed in the official 2026 HRSA Health Center Service Delivery "
            "and Look-Alike Sites dataset."
        ),
        "organization_type": "HRSA-supported health center",
        "service_name": site_name,
        "description": (
            "The official 2026 HRSA dataset lists this as an active health-center site. "
            "Contact the site to confirm services, eligibility, hours, cost, and availability."
        ),
        "languages": [],
        "emergency_availability": False,
        "remote_service_available": False,
        "categories": ["Healthcare access"],
        "contact_phone": _clean(row.get("Site Telephone Number")) or None,
        "website": _website(row.get("Site Web Address")),
        "location_name": site_name,
        "city": _clean(row.get("Site City")) or None,
        "region": region,
        "postal_code": _clean(row.get("Site Postal Code")) or None,
        "country": "US",
        "timezone": None,
        "service_area": _clean(row.get("Complete County Name")) or None,
        "hours": f"Reported operating hours per week: {hours}" if hours else None,
        "source_name": "HRSA Health Center Service Delivery and Look-Alike Sites (2026)",
        "source_url": HRSA_SOURCE_URL,
        "source_organization": "U.S. Health Resources and Services Administration",
        "source_type": "government_dataset",
        "source_retrieved_at": retrieved_at,
        "source_notes": (
            f"Source record date: {source_record_date}; HRSA identifier: {identifier}. "
            "Candidate only; requires human field verification before publication."
        ),
        "source_public": True,
        "source_supports_changed_fields": True,
    }


def _write_chunks(rows: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_bytes = 2

    def emit() -> None:
        nonlocal current_bytes
        if not current:
            return
        payload = json.dumps(current, ensure_ascii=False, separators=(",", ":")).encode()
        index = len(chunks) + 1
        name = f"hrsa-health-centers-2026-{index:03d}.json"
        (output_dir / name).write_bytes(payload)
        chunks.append(
            {
                "filename": name,
                "rows": len(current),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
        current.clear()
        current_bytes = 2

    for row in rows:
        row_bytes = len(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode())
        projected_bytes = current_bytes + row_bytes + (1 if current else 0)
        if current and (len(current) >= MAX_CHUNK_ROWS or projected_bytes > MAX_CHUNK_BYTES):
            emit()
            projected_bytes = 2 + row_bytes
        current.append(row)
        current_bytes = projected_bytes
    emit()
    return chunks


def prepare_hrsa_2026_snapshot(
    input_path: Path,
    output_dir: Path,
    *,
    source_updated_at: str,
    retrieved_at: str,
) -> StagingSummary:
    if not source_updated_at.startswith("2026-"):
        raise ValueError("HRSA source update must be in 2026")
    payload = input_path.read_bytes()
    source_hash = hashlib.sha256(payload).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    for previous in output_dir.glob("hrsa-health-centers-2026-*.json"):
        previous.unlink()

    raw_rows = skipped_non_2026 = skipped_inactive = rejected_rows = 0
    staged: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"HRSA snapshot is missing columns: {sorted(missing)}")
        for row in reader:
            raw_rows += 1
            created = _record_date(row["Data Warehouse Record Create Date"])
            if created is None or created.year != 2026:
                skipped_non_2026 += 1
                continue
            if _clean(row["Site Status Description"]).casefold() != "active":
                skipped_inactive += 1
                continue
            candidate = _candidate(row, retrieved_at)
            if candidate is None or candidate["source_identifier"] in identifiers:
                rejected_rows += 1
                continue
            identifiers.add(str(candidate["source_identifier"]))
            staged.append(candidate)

    chunks = _write_chunks(staged, output_dir)
    manifest = {
        "source_identifier": HRSA_SOURCE_IDENTIFIER,
        "source_url": HRSA_SOURCE_URL,
        "source_updated_at": source_updated_at,
        "retrieved_at": retrieved_at,
        "source_sha256": source_hash,
        "raw_rows": raw_rows,
        "staged_rows": len(staged),
        "skipped_non_2026": skipped_non_2026,
        "skipped_inactive": skipped_inactive,
        "rejected_rows": rejected_rows,
        "publication_status": "blocked_pending_human_source_and_record_review",
        "chunks": chunks,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return StagingSummary(
        raw_rows=raw_rows,
        staged_rows=len(staged),
        skipped_non_2026=skipped_non_2026,
        skipped_inactive=skipped_inactive,
        rejected_rows=rejected_rows,
        chunks=len(chunks),
        source_sha256=source_hash,
        manifest_path=str(manifest_path),
    )
