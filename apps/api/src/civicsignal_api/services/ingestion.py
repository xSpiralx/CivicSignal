import uuid
from dataclasses import dataclass
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
    ImportBatch,
    ImportBatchStatus,
    SourceApprovalStatus,
)
from civicsignal_api.schemas.governance import DraftContent
from civicsignal_api.security import utcnow
from civicsignal_api.services.imports import classify_duplicate, parse_import, record_fingerprint

IMPORTER_VERSION = "1.0.0"


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
    rows: list[tuple[str, dict[str, Any], str, str]] = []
    errors: list[dict[str, Any]] = []
    classifications: dict[str, int] = {}
    seen_identifiers: set[str] = set()
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
            content = DraftContent.model_validate(raw).model_dump(mode="json")
        except ValidationError as exc:
            errors.append(
                {
                    "row": index,
                    "source_identifier": source_id,
                    "error": "row failed the governed draft schema",
                    "fields": [
                        ".".join(str(part) for part in item["loc"]) for item in exc.errors()
                    ],
                }
            )
            continue
        classification = classify_duplicate(raw, published_content)
        classifications[classification] = classifications.get(classification, 0) + 1
        rows.append((source_id, content, record_fingerprint(raw), classification))
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
    if await db.scalar(
        select(ImportBatch.id).where(
            ImportBatch.source_id == source.id,
            ImportBatch.content_hash == parsed.content_hash,
        )
    ):
        raise ValueError("This exact source payload was already imported")
    batch = ImportBatch(
        source_id=source.id,
        status=ImportBatchStatus.NEEDS_REVIEW,
        fetched_at=utcnow(),
        license_snapshot=source.license_name,
        attribution_snapshot=source.attribution_requirement,
        content_hash=parsed.content_hash,
        importer_version=IMPORTER_VERSION,
        original_filename=file_path.name,
        row_count=len(parsed.rows),
        accepted_count=len(rows),
        rejected_count=len(errors),
        validation_result={"errors": errors, "classifications": classifications},
        created_by_id=actor_id,
    )
    db.add(batch)
    await db.flush()
    for source_id, content, fingerprint, classification in rows:
        db.add(
            CandidateResource(
                batch_id=batch.id,
                source_id=source.id,
                source_identifier=source_id,
                content=content,
                normalized_fingerprint=fingerprint,
                duplicate_classification=classification,
                validation_result={"valid": True},
            )
        )
    db.add(
        AuditEvent(
            actor_id=actor_id,
            action="import.batch.create",
            subject_type="import_batch",
            subject_id=str(batch.id),
            summary=(
                f"Controlled import created {len(rows)} candidates and {len(errors)} row errors; "
                "zero drafts and zero public records created"
            ),
        )
    )
    await db.commit()
    return ImportPreview(**{**preview.__dict__, "batch_id": str(batch.id)})
