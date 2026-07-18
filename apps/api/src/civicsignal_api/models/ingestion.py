import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from civicsignal_api.db.base import Base


def enum_values(items: type[enum.Enum]) -> list[str]:
    return [str(item.value) for item in items]


class SourceApprovalStatus(str, enum.Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    RESTRICTED = "restricted"
    REJECTED = "rejected"
    DISABLED = "disabled"


class ImportBatchStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    NEEDS_REVIEW = "needs_review"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


class CandidateReviewStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED_AS_DRAFT = "accepted_as_draft"
    REJECTED = "rejected"
    CONFLICT = "conflict"


class ApprovedSource(Base):
    """A governance decision about a possible ingestion source.

    The name describes the registry, not the record's current status. A source
    may be proposed, restricted, rejected, or disabled as well as approved.
    """

    __tablename__ = "approved_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    stable_identifier: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(240))
    publishing_organization: Mapped[str] = mapped_column(String(240))
    source_url: Mapped[str] = mapped_column(String(2048))
    source_type: Mapped[str] = mapped_column(String(80))
    geographic_scope: Mapped[str] = mapped_column(String(240))
    resource_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    license_name: Mapped[str | None] = mapped_column(String(240))
    license_url: Mapped[str | None] = mapped_column(String(2048))
    terms_url: Mapped[str | None] = mapped_column(String(2048))
    attribution_requirement: Mapped[str | None] = mapped_column(Text)
    automation_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    rate_limit: Mapped[str | None] = mapped_column(String(240))
    allowed_hosts: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_legal_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_technical_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_status: Mapped[SourceApprovalStatus] = mapped_column(
        Enum(SourceApprovalStatus, native_enum=False, values_callable=enum_values),
        default=SourceApprovalStatus.PROPOSED,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_accounts.id", ondelete="SET NULL"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    import_method: Mapped[str] = mapped_column(String(80), default="manual")
    reliability_classification: Mapped[str] = mapped_column(String(80), default="unassessed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def may_run_automatically(self) -> bool:
        return bool(
            self.enabled
            and self.automation_permission
            and self.approval_status == SourceApprovalStatus.APPROVED
            and self.allowed_hosts
        )


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approved_sources.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[ImportBatchStatus] = mapped_column(
        Enum(ImportBatchStatus, native_enum=False, values_callable=enum_values),
        default=ImportBatchStatus.PENDING,
        index=True,
    )
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    license_snapshot: Mapped[str | None] = mapped_column(Text)
    attribution_snapshot: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    importer_version: Mapped[str] = mapped_column(String(40))
    original_filename: Mapped[str | None] = mapped_column(String(240))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    review_decision: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_accounts.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CandidateResource(Base):
    __tablename__ = "candidate_resources"
    __table_args__ = (UniqueConstraint("source_id", "source_identifier"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approved_sources.id", ondelete="RESTRICT"), index=True
    )
    source_identifier: Mapped[str] = mapped_column(String(240))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    normalized_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    duplicate_classification: Mapped[str] = mapped_column(String(50), index=True)
    validation_result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    review_status: Mapped[CandidateReviewStatus] = mapped_column(
        Enum(CandidateReviewStatus, native_enum=False, values_callable=enum_values),
        default=CandidateReviewStatus.PENDING,
        index=True,
    )
    review_decision: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_accounts.id", ondelete="SET NULL"), index=True
    )
    governed_resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("governed_resources.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
