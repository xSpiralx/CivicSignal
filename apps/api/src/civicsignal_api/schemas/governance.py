import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class DraftContent(BaseModel):
    organization_name: str = Field(min_length=1, max_length=200)
    organization_description: str = Field(min_length=1, max_length=5000)
    organization_type: str = Field(min_length=1, max_length=100)
    service_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    eligibility: str | None = Field(default=None, max_length=5000)
    languages: list[str] = Field(default_factory=list, max_length=30)
    accessibility: str | None = Field(default=None, max_length=5000)
    emergency_availability: bool = False
    source_name: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    source_organization: str = Field(min_length=1, max_length=200)


class DraftCreate(BaseModel):
    content: DraftContent


class DraftUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    content: DraftContent


class TransitionRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=2000)
    evidence: list[str] = Field(default_factory=list, max_length=20)
    next_due_at: datetime | None = None


class GovernedResourceView(BaseModel):
    id: uuid.UUID
    state: str
    revision: int
    content: DraftContent
    owner_id: uuid.UUID
    assigned_reviewer_id: uuid.UUID | None
    public_service_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
