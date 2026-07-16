from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from civicsignal_api.models.resource import ContactType, VerificationStatus


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slug: str
    name: str
    description: str | None


class SourceResponse(BaseModel):
    name: str
    url: str
    organization: str
    last_checked_at: datetime


class ContactResponse(BaseModel):
    channel_type: ContactType
    label: str
    value: str
    is_primary: bool


class LocationResponse(BaseModel):
    display_name: str
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    region: str | None
    postal_code: str | None
    country: str
    service_area: str | None
    transportation: str | None
    accessibility: str | None
    hours: str | None
    timezone: str


class VerificationResponse(BaseModel):
    status: Literal[VerificationStatus.VERIFIED, VerificationStatus.NEEDS_REVERIFICATION]
    last_checked_at: datetime
    may_be_stale: bool
    next_due_at: datetime | None
    freshness: Literal["current", "due_soon", "due", "overdue", "critically_stale", "unknown"]


class OrganizationSummary(BaseModel):
    id: UUID
    public_name: str
    description: str
    organization_type: str
    website: str | None
    public_phone: str | None
    public_email: str | None
    languages: list[str]
    accessibility: str | None


class ServiceResponse(BaseModel):
    id: UUID
    organization: OrganizationSummary
    name: str
    description: str
    eligibility: str | None
    required_documents: str | None
    cost_information: str | None
    languages: list[str]
    accessibility: str | None
    application_instructions: str | None
    appointment_requirements: str | None
    emergency_availability: bool
    categories: list[CategoryResponse]
    locations: list[LocationResponse]
    contacts: list[ContactResponse]
    sources: list[SourceResponse]
    verification: VerificationResponse


class ServiceListItem(BaseModel):
    id: UUID
    organization_name: str
    name: str
    description: str
    categories: list[CategoryResponse]
    location_summary: str | None
    languages: list[str]
    accessibility: str | None
    primary_contact: ContactResponse | None
    verification: VerificationResponse


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class ServiceListResponse(BaseModel):
    items: list[ServiceListItem]
    pagination: PaginationMeta


class OrganizationListResponse(BaseModel):
    items: list[OrganizationSummary]
    pagination: PaginationMeta
