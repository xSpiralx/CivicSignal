import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import GovernedResource, ResourceRevision, WorkflowState
from civicsignal_api.models.ingestion import (
    ApprovedSource,
    CandidateResource,
    CandidateReviewStatus,
    ImportBatch,
    ImportBatchStatus,
    SourceApprovalStatus,
)
from civicsignal_api.schemas.governance import DraftContent
from civicsignal_api.security import utcnow
from civicsignal_api.services.imports import classify_duplicate, parse_import, record_fingerprint

IMPORTER_VERSION = "1.0.0"
CURRENT_DATA_YEARS = {2025, 2026}
HIGH_RISK_TERMS = {
    "crisis",
    "suicide prevention",
    "domestic violence",
    "substance-use treatment",
    "substance use treatment",
    "mental health",
    "medical care",
    "healthcare access",
    "legal assistance",
    "immigration assistance",
    "emergency shelter",
    "child protection",
}


def _date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return result.replace(tzinfo=result.tzinfo or UTC)


def _freshness(
    raw: dict[str, Any], source: ApprovedSource
) -> tuple[datetime | None, datetime | None]:
    record = _date(raw.get("source_record_updated_at") or raw.get("source_record_date"))
    dataset = _date(raw.get("dataset_updated_at")) or source.latest_source_update_at
    accepted = record or dataset
    if accepted is None or accepted.year not in CURRENT_DATA_YEARS:
        raise ValueError("No trustworthy 2025-2026 source freshness date")
    return record, dataset


def _risk(categories: list[str]) -> str:
    normalized = " ".join(categories).casefold()
    return "high" if any(term in normalized for term in HIGH_RISK_TERMS) else "standard"


@dataclass(frozen=True)
class ImportPreview:
    source: str
    content_hash: str
    rows: int
    valid: int
    rejected: int
    classifications: dict[str, int]
    errors: list[dict[str, Any]]
    batch_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "content_hash": self.content_hash,
            "rows": self.rows,
            "valid": self.valid,
            "rejected": self.rejected,
            "classifications": self.classifications,
            "errors": self.errors,
            "batch_id": self.batch_id,
            "drafts_created": 0,
            "published": 0,
        }


async def preview_or_import_file(
    db: AsyncSession,
    *,
    source_identifier: str,
    actor_id: uuid.UUID,
    file_path: Path,
    media_type: str,
    commit: bool,
) -> ImportPreview:
    source = await db.scalar(
        select(ApprovedSource).where(ApprovedSource.stable_identifier == source_identifier)
    )
    if source is None:
        raise ValueError("Source is not registered")
    if source.approval_status != SourceApprovalStatus.APPROVED:
        raise ValueError("Source is not approved; import is blocked")
    if not source.enabled or not source.redistribution_permitted:
        raise ValueError("Source is not enabled with documented redistribution permission")
    payload = file_path.read_bytes()
    parsed = parse_import(payload, media_type, file_path.name)
    published_content = list(
        await db.scalars(
            select(ResourceRevision.content)
            .join(
                GovernedResource,
                GovernedResource.published_revision_id == ResourceRevision.id,
            )
            .where(GovernedResource.state == WorkflowState.PUBLISHED)
        )
    )
    existing_fingerprints = set(
        await db.scalars(
            select(CandidateResource.normalized_fingerprint).where(
                CandidateResource.source_id == source.id
            )
        )
    )
    existing_identifiers = set(
        await db.scalars(
            select(CandidateResource.source_identifier).where(
                CandidateResource.source_id == source.id
            )
        )
    )
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    classifications: dict[str, int] = {}
    seen_identifiers: set[str] = set()
    seen_fingerprints: set[str] = set()
    for index, raw in enumerate(parsed.rows, start=1):
        source_id = str(raw.get("source_identifier") or raw.get("id") or "").strip()
        if not source_id or len(source_id) > 240:
            errors.append({"row": index, "error": "source_identifier is required"})
            continue
        if source_id in seen_identifiers:
            errors.append({"row": index, "error": "duplicate source_identifier in batch"})
            continue
        seen_identifiers.add(source_id)
        try:
            source_record_updated_at, dataset_updated_at = _freshness(raw, source)
            content = DraftContent.model_validate(raw).model_dump(mode="json")
        except (ValidationError, ValueError) as exc:
            errors.append(
                {
                    "row": index,
                    "source_identifier": source_id,
                    "error": str(exc)
                    if isinstance(exc, ValueError)
                    else "row failed the governed draft schema",
                    "fields": [".".join(str(part) for part in item["loc"]) for item in exc.errors()]
                    if isinstance(exc, ValidationError)
                    else [],
                }
            )
            continue
        fingerprint = record_fingerprint(raw)
        classification = (
            "exact_match"
            if fingerprint in existing_fingerprints or fingerprint in seen_fingerprints
            else classify_duplicate(raw, published_content)
        )
        seen_fingerprints.add(fingerprint)
        classifications[classification] = classifications.get(classification, 0) + 1
        categories = [str(item)[:120] for item in raw.get("categories", [])][:20]
        rows.append(
            {
                "source_identifier": source_id,
                "content": content,
                "raw_content": raw,
                "fingerprint": fingerprint,
                "classification": classification,
                "source_record_updated_at": source_record_updated_at,
                "dataset_updated_at": dataset_updated_at,
                "categories": categories,
            }
        )
    preview = ImportPreview(
        source=source.stable_identifier,
        content_hash=parsed.content_hash,
        rows=len(parsed.rows),
        valid=len(rows),
        rejected=len(errors),
        classifications=classifications,
        errors=errors,
    )
    if not commit:
        return preview
    existing_batch = await db.scalar(
        select(ImportBatch).where(
            ImportBatch.source_id == source.id,
            ImportBatch.content_hash == parsed.content_hash,
        )
    )
    if existing_batch:
        return ImportPreview(**{**preview.__dict__, "batch_id": str(existing_batch.id)})
    now = utcnow()
    batch = ImportBatch(
        source_id=source.id,
        status=ImportBatchStatus.NEEDS_REVIEW,
        fetched_at=now,
        license_snapshot=source.license_name,
        attribution_snapshot=source.attribution_requirement,
        content_hash=parsed.content_hash,
        idempotency_key=f"{source.stable_identifier}:{parsed.content_hash}",
        importer_version=IMPORTER_VERSION,
        original_filename=file_path.name,
        row_count=len(parsed.rows),
        accepted_count=len(rows),
        rejected_count=len(errors),
        processed_count=len(parsed.rows),
        failed_count=len(errors),
        checkpoint_row=len(parsed.rows),
        resume_token=f"{source.stable_identifier}:{parsed.content_hash[:24]}",
        validation_result={"errors": errors, "classifications": classifications},
        created_by_id=actor_id,
        started_at=now,
        completed_at=now,
    )
    db.add(batch)
    await db.flush()
    created = 0
    for row in rows:
        if row["source_identifier"] in existing_identifiers:
            continue
        content = row["content"]
        classification = row["classification"]
        conflict = "published_conflict" if classification == "conflict_with_published" else "none"
        review_status = (
            CandidateReviewStatus.NEEDS_DUPLICATE_REVIEW
            if classification != "new_resource"
            else CandidateReviewStatus.READY_FOR_REVIEW
        )
        db.add(
            CandidateResource(
                batch_id=batch.id,
                source_id=source.id,
                source_identifier=row["source_identifier"],
                content=content,
                raw_content=row["raw_content"],
                source_url=str(content.get("source_url") or source.source_url),
                source_content_hash=row["fingerprint"],
                source_record_updated_at=row["source_record_updated_at"],
                dataset_updated_at=row["dataset_updated_at"],
                retrieved_at=_date(content.get("source_retrieved_at")) or now,
                city=content.get("city"),
                county=str(row["raw_content"].get("county") or content.get("service_area") or "")[
                    :160
                ]
                or None,
                region=content.get("region"),
                postal_code=content.get("postal_code"),
                categories=row["categories"],
                service_area_type=str(row["raw_content"].get("service_area_type") or "local")[:40],
                nationwide=bool(row["raw_content"].get("nationwide", False)),
                remote=bool(content.get("remote_service_available", False)),
                risk_classification=_risk(row["categories"]),
                conflict_status=conflict,
                normalized_fingerprint=row["fingerprint"],
                duplicate_classification=classification,
                validation_result={"valid": True},
                review_status=review_status,
            )
        )
        created += 1
    batch.accepted_count = created
    source.latest_successful_retrieval_at = now
    db.add(
        AuditEvent(
            actor_id=actor_id,
            action="import.batch.create",
            subject_type="import_batch",
            subject_id=str(batch.id),
            summary=(
                f"Controlled import created {created} candidates and {len(errors)} row errors; "
                "zero drafts and zero public records created"
            ),
        )
    )
    await db.commit()
    return ImportPreview(**{**preview.__dict__, "batch_id": str(batch.id)})
