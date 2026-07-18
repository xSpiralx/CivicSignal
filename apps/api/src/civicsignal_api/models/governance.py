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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from civicsignal_api.db.base import Base


class WorkflowState(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHANGES_REQUESTED = "changes_requested"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    PUBLISHED = "published"
    NEEDS_REVERIFICATION = "needs_reverification"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class CorrectionCategory(str, enum.Enum):
    INCORRECT_PHONE = "incorrect_phone"
    INCORRECT_ADDRESS = "incorrect_address"
    INCORRECT_HOURS = "incorrect_hours"
    BROKEN_WEBSITE = "broken_website"
    RESOURCE_CLOSED = "resource_closed"
    SERVICE_UNAVAILABLE = "service_unavailable"
    ELIGIBILITY_CHANGED = "eligibility_changed"
    ACCESSIBILITY_INCORRECT = "accessibility_incorrect"
    LANGUAGE_INCORRECT = "language_incorrect"
    OTHER = "other"


class CorrectionStatus(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    NEEDS_REVERIFICATION = "needs_reverification"
    DUPLICATE = "duplicate"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ABUSE = "abuse"


class ReverificationStatus(str, enum.Enum):
    OPEN = "open"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReverificationOutcome(str, enum.Enum):
    CONFIRMED_UNCHANGED = "confirmed_unchanged"
    UPDATED_CONFIRMED = "updated_confirmed"
    COULD_NOT_CONFIRM = "could_not_confirm"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    SOURCE_UNAVAILABLE = "source_unavailable"
    RESOURCE_CLOSED = "resource_closed"
    ARCHIVED = "archived"
    ESCALATED = "escalated"


class GovernedResource(Base):
    __tablename__ = "governed_resources"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    state: Mapped[WorkflowState] = mapped_column(Enum(WorkflowState, native_enum=False), index=True)
    current_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resource_revisions.id", use_alter=True)
    )
    published_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resource_revisions.id", use_alter=True)
    )
    public_service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id"), unique=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_accounts.id"), index=True)
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_accounts.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    revisions: Mapped[list["ResourceRevision"]] = relationship(
        back_populates="resource",
        foreign_keys="ResourceRevision.resource_id",
        order_by="ResourceRevision.number",
    )


class ResourceRevision(Base):
    __tablename__ = "resource_revisions"
    __table_args__ = (UniqueConstraint("resource_id", "number"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("governed_resources.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_accounts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resource: Mapped[GovernedResource] = relationship(
        back_populates="revisions", foreign_keys=[resource_id]
    )


class GovernanceDecision(Base):
    __tablename__ = "governance_decisions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("governed_resources.id"), index=True)
    revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resource_revisions.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_accounts.id"))
    action: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReverificationTask(Base):
    __tablename__ = "reverification_tasks"
    __table_args__ = (
        UniqueConstraint("service_id", "active", name="uq_active_reverification_per_service"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), index=True
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("governed_resources.id", ondelete="SET NULL"), index=True
    )
    published_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resource_revisions.id", ondelete="SET NULL")
    )
    trigger_source: Mapped[str] = mapped_column(String(40), default="stale_detection")
    reason: Mapped[str] = mapped_column(String(80))
    freshness_state: Mapped[str] = mapped_column(String(30), index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[ReverificationStatus] = mapped_column(
        Enum(ReverificationStatus, native_enum=False), default=ReverificationStatus.OPEN, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool | None] = mapped_column(Boolean, default=True, index=True)
    assigned_verifier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_accounts.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[ReverificationOutcome | None] = mapped_column(
        Enum(ReverificationOutcome, native_enum=False)
    )
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    contact_attempt_summary: Mapped[str | None] = mapped_column(Text)
    source_references: Mapped[list[str] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)


class CorrectionReport(Base):
    __tablename__ = "correction_reports"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    published_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resource_revisions.id", ondelete="SET NULL")
    )
    category: Mapped[CorrectionCategory] = mapped_column(
        Enum(CorrectionCategory, native_enum=False), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    reporter_name: Mapped[str | None] = mapped_column(String(120))
    reporter_email: Mapped[str | None] = mapped_column(String(320))
    content_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[CorrectionStatus] = mapped_column(
        Enum(CorrectionStatus, native_enum=False), default=CorrectionStatus.NEW, index=True
    )
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_accounts.id", ondelete="SET NULL"), index=True
    )
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("correction_reports.id", ondelete="SET NULL")
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reverification_tasks.id", ondelete="SET NULL"), index=True
    )
    resolution_reason: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
