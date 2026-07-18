import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from civicsignal_api.models.governance import (
    CorrectionCategory,
    CorrectionStatus,
    ReverificationOutcome,
    ReverificationStatus,
)
from civicsignal_api.schemas.governance import DraftContent


class PublicCorrectionCreate(BaseModel):
    category: CorrectionCategory
    description: str = Field(min_length=10, max_length=4000)
    reporter_name: str | None = Field(default=None, max_length=120)
    reporter_email: str | None = Field(default=None, max_length=320)
    website: str = Field(default="", max_length=0)
    form_started_at: datetime | None = None

    @field_validator("description", "reporter_name", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("reporter_email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if not value:
            return None
        normalized = value.strip().casefold()
        if not re.fullmatch(r"[^\s@]{1,64}@[^\s@.]+(?:\.[^\s@.]+)+", normalized):
            raise ValueError("Enter a valid email address")
        return normalized


class PublicCorrectionResponse(BaseModel):
    id: uuid.UUID
    status: str = "received"
    message: str = "Your report was received for review. Public information has not changed."


class CorrectionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_id: uuid.UUID
    category: CorrectionCategory
    description: str
    reporter_name: str | None
    reporter_email: str | None = None
    status: CorrectionStatus
    assigned_reviewer_id: uuid.UUID | None
    duplicate_of_id: uuid.UUID | None
    task_id: uuid.UUID | None
    resolution_reason: str | None
    resolved_at: datetime | None
    version: int
    submitted_at: datetime


class CorrectionAction(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str | None = Field(default=None, min_length=3, max_length=2000)
    assignee_id: uuid.UUID | None = None
    duplicate_of_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None


class ReverificationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_id: uuid.UUID
    resource_id: uuid.UUID | None
    published_revision_id: uuid.UUID | None
    trigger_source: str
    reason: str
    freshness_state: str
    due_at: datetime
    status: ReverificationStatus
    assigned_verifier_id: uuid.UUID | None
    claimed_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    outcome: ReverificationOutcome | None
    evidence_summary: str | None
    contact_attempt_summary: str | None
    source_references: list[str] | None
    notes: str | None
    version: int
    created_at: datetime


class ReverificationAction(BaseModel):
    expected_version: int = Field(ge=1)
    assignee_id: uuid.UUID | None = None
    evidence_summary: str | None = Field(default=None, max_length=5000)
    contact_attempt_summary: str | None = Field(default=None, max_length=5000)
    source_references: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=5000)
    reason: str | None = Field(default=None, max_length=2000)
    next_due_at: datetime | None = None
    expected_revision: int | None = Field(default=None, ge=1)
    proposed_content: DraftContent | None = None


class ProposalSave(BaseModel):
    expected_task_version: int = Field(ge=1)
    expected_revision: int = Field(ge=1)
    content: DraftContent


class ProposalView(BaseModel):
    task_id: uuid.UUID
    task_version: int
    resource_id: uuid.UUID
    published_revision: int
    proposed_revision: int
    published_content: DraftContent
    proposed_content: DraftContent
    changed_fields: list[str]
    blocking_errors: list[str]
    warnings: list[str]
    ready: bool
