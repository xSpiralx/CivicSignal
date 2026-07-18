import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from civicsignal_api.models.ingestion import SourceApprovalStatus


class SourceCreate(BaseModel):
    stable_identifier: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,119}$")
    name: str = Field(min_length=2, max_length=240)
    publishing_organization: str = Field(min_length=2, max_length=240)
    source_url: HttpUrl
    download_url: HttpUrl | None = None
    source_type: str = Field(min_length=2, max_length=80)
    geographic_scope: str = Field(min_length=2, max_length=240)
    jurisdiction: str | None = Field(default=None, max_length=240)
    states_covered: list[str] = Field(default_factory=list, max_length=60)
    localities_covered: list[str] = Field(default_factory=list, max_length=500)
    resource_categories: list[str] = Field(max_length=50)
    license_name: str | None = Field(default=None, max_length=240)
    license_url: HttpUrl | None = None
    terms_url: HttpUrl | None = None
    attribution_requirement: str | None = Field(default=None, max_length=2000)
    redistribution_permitted: bool = False
    modification_permitted: bool = False
    automation_permission: bool = False
    rate_limit: str | None = Field(default=None, max_length=240)
    allowed_hosts: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    import_method: str = Field(default="manual", min_length=2, max_length=80)
    reliability_classification: str = Field(default="unassessed", min_length=2, max_length=80)
    latest_source_update_at: datetime | None = None
    latest_successful_retrieval_at: datetime | None = None
    freshness_policy: str | None = Field(default=None, max_length=4000)


class SourceDecision(BaseModel):
    approval_status: SourceApprovalStatus
    reason: str = Field(min_length=10, max_length=2000)
    enabled: bool = False
    automation_permission: bool = False
    allowed_hosts: list[str] = Field(default_factory=list, max_length=20)
    rate_limit: str | None = Field(default=None, max_length=240)
    license_name: str | None = Field(default=None, max_length=240)
    license_url: HttpUrl | None = None
    terms_url: HttpUrl | None = None
    attribution_requirement: str | None = Field(default=None, max_length=2000)
    redistribution_permitted: bool = False
    modification_permitted: bool = False
    last_legal_review_at: datetime
    last_technical_review_at: datetime

    @model_validator(mode="after")
    def approved_automation_is_documented(self) -> "SourceDecision":
        if self.enabled and self.approval_status != SourceApprovalStatus.APPROVED:
            raise ValueError("Only approved sources can be enabled")
        if self.automation_permission and not self.allowed_hosts:
            raise ValueError("Automated sources require an explicit hostname allowlist")
        if self.enabled and not self.automation_permission:
            raise ValueError("Enabled ingestion requires documented automation permission")
        if self.approval_status == SourceApprovalStatus.APPROVED and not self.license_name:
            raise ValueError("Approved sources require documented permission or a license")
        if (
            self.approval_status == SourceApprovalStatus.APPROVED
            and not self.redistribution_permitted
        ):
            raise ValueError("Approved sources require documented redistribution permission")
        return self


class SourceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stable_identifier: str
    name: str
    publishing_organization: str
    source_url: str
    download_url: str | None
    source_type: str
    geographic_scope: str
    jurisdiction: str | None
    states_covered: list[str]
    localities_covered: list[str]
    resource_categories: list[str]
    license_name: str | None
    license_url: str | None
    terms_url: str | None
    attribution_requirement: str | None
    redistribution_permitted: bool
    modification_permitted: bool
    automation_permission: bool
    rate_limit: str | None
    allowed_hosts: list[str]
    last_legal_review_at: datetime | None
    last_technical_review_at: datetime | None
    approval_status: SourceApprovalStatus
    reviewer_id: uuid.UUID | None
    notes: str | None
    enabled: bool
    import_method: str
    reliability_classification: str
    latest_source_update_at: datetime | None
    latest_successful_retrieval_at: datetime | None
    freshness_policy: str | None
    created_at: datetime
    updated_at: datetime
