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
    required_documents: str | None = Field(default=None, max_length=5000)
    cost_information: str | None = Field(default=None, max_length=5000)
    languages: list[str] = Field(default_factory=list, max_length=30)
    accessibility: str | None = Field(default=None, max_length=5000)
    emergency_availability: bool = False
    remote_service_available: bool = False
    categories: list[str] = Field(default_factory=list, max_length=20)
    contact_phone: str | None = Field(default=None, max_length=50)
    contact_email: str | None = Field(default=None, max_length=320)
    website: HttpUrl | None = None
    location_name: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=30)
    service_area: str | None = Field(default=None, max_length=2000)
    hours: str | None = Field(default=None, max_length=2000)
    transportation: str | None = Field(default=None, max_length=2000)
    application_instructions: str | None = Field(default=None, max_length=5000)
    source_name: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    source_organization: str = Field(min_length=1, max_length=200)
    source_type: str = Field(default="provider_submission", max_length=50)
    source_retrieved_at: datetime | None = None
    source_notes: str | None = Field(default=None, max_length=2000)
    source_public: bool = True
    source_supports_changed_fields: bool = True


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
