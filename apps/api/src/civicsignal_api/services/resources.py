import math
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from civicsignal_api.models.resource import (
    Category,
    Location,
    Organization,
    Service,
    Source,
    Verification,
    VerificationStatus,
)
from civicsignal_api.schemas.resources import (
    CategoryResponse,
    ContactResponse,
    LocationResponse,
    OrganizationSummary,
    PaginationMeta,
    ServiceListItem,
    ServiceListResponse,
    ServiceResponse,
    SourceResponse,
    VerificationResponse,
)

PUBLIC_STATES = (VerificationStatus.VERIFIED, VerificationStatus.NEEDS_REVERIFICATION)


def _options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Service.organization),
        selectinload(Service.categories),
        selectinload(Service.locations),
        selectinload(Service.contacts),
        selectinload(Service.sources),
        selectinload(Service.verifications),
    )


def _latest(service: Service) -> Verification:
    return max(service.verifications, key=lambda record: record.checked_at)


def _verification(service: Service) -> VerificationResponse:
    latest = _latest(service)
    now = datetime.now(UTC)
    expires_at = latest.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    stale = latest.status == VerificationStatus.NEEDS_REVERIFICATION or (
        expires_at is not None and expires_at < now
    )
    freshness: Literal["current", "due_soon", "due", "overdue", "critically_stale", "unknown"]
    if expires_at is None:
        freshness = "unknown"
    else:
        days = (expires_at - now).total_seconds() / 86_400
        if days < -30:
            freshness = "critically_stale"
        elif days < -7:
            freshness = "overdue"
        elif days <= 0:
            freshness = "due"
        elif days <= 14:
            freshness = "due_soon"
        else:
            freshness = "current"
    return VerificationResponse(
        status=cast(
            Literal[VerificationStatus.VERIFIED, VerificationStatus.NEEDS_REVERIFICATION],
            latest.status,
        ),
        last_checked_at=latest.checked_at,
        may_be_stale=stale,
        next_due_at=expires_at,
        freshness=freshness,
    )


def _organization(organization: Organization) -> OrganizationSummary:
    return OrganizationSummary(
        id=organization.id,
        public_name=organization.public_name,
        description=organization.description,
        organization_type=organization.organization_type,
        website=organization.website,
        public_phone=organization.public_phone,
        public_email=organization.public_email,
        languages=_split(organization.languages),
        accessibility=organization.accessibility,
    )


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _base_public_query() -> Select[tuple[Service]]:
    latest = (
        select(Verification.service_id, func.max(Verification.checked_at).label("latest"))
        .group_by(Verification.service_id)
        .subquery()
    )
    return (
        select(Service)
        .join(Organization)
        .join(latest, latest.c.service_id == Service.id)
        .join(
            Verification,
            (Verification.service_id == Service.id) & (Verification.checked_at == latest.c.latest),
        )
        .where(
            Service.is_active.is_(True),
            Organization.is_active.is_(True),
            Verification.status.in_(PUBLIC_STATES),
            select(func.count(Source.id)).where(Source.service_id == Service.id).scalar_subquery()
            > 0,
        )
    )


async def list_services(
    session: AsyncSession,
    *,
    query: str | None,
    category: str | None,
    city: str | None,
    region: str | None,
    postal_code: str | None,
    language: str | None,
    accessibility: str | None,
    eligibility: str | None,
    sort: Literal["name", "organization", "state_city", "recently_verified"],
    page: int,
    page_size: int,
) -> ServiceListResponse:
    statement = _base_public_query()
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Organization.public_name.ilike(pattern),
                Service.name.ilike(pattern),
                Service.description.ilike(pattern),
                Service.eligibility.ilike(pattern),
                Service.categories.any(Category.name.ilike(pattern)),
                Service.locations.any(
                    or_(
                        Location.city.ilike(pattern),
                        Location.region.ilike(pattern),
                        Location.postal_code.ilike(pattern),
                    )
                ),
                Service.languages.ilike(pattern),
            )
        )
    if category:
        statement = statement.where(Service.categories.any(Category.slug == category))
    if city:
        statement = statement.where(Service.locations.any(Location.city.ilike(city)))
    if region:
        statement = statement.where(Service.locations.any(Location.region.ilike(region)))
    if postal_code:
        statement = statement.where(Service.locations.any(Location.postal_code == postal_code))
    if language:
        statement = statement.where(Service.languages.ilike(f"%{language}%"))
    if accessibility:
        statement = statement.where(Service.accessibility.ilike(f"%{accessibility}%"))
    if eligibility:
        statement = statement.where(Service.eligibility.ilike(f"%{eligibility}%"))
    total = await session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    location_region = (
        select(func.min(Location.region))
        .where(Location.service_id == Service.id, Location.is_active.is_(True))
        .correlate(Service)
        .scalar_subquery()
    )
    location_city = (
        select(func.min(Location.city))
        .where(Location.service_id == Service.id, Location.is_active.is_(True))
        .correlate(Service)
        .scalar_subquery()
    )
    latest_check = (
        select(func.max(Verification.checked_at))
        .where(Verification.service_id == Service.id)
        .correlate(Service)
        .scalar_subquery()
    )
    ordering = {
        "name": (Service.name.asc(), Service.id.asc()),
        "organization": (Organization.public_name.asc(), Service.name.asc(), Service.id.asc()),
        "state_city": (
            location_region.asc().nulls_last(),
            location_city.asc().nulls_last(),
            Service.name.asc(),
            Service.id.asc(),
        ),
        "recently_verified": (
            latest_check.desc().nulls_last(),
            Service.name.asc(),
            Service.id.asc(),
        ),
    }[sort]
    rows = await session.scalars(
        statement.options(*_options())
        .order_by(*ordering)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = []
    for service in rows.unique().all():
        primary = next((contact for contact in service.contacts if contact.is_primary), None)
        location = next((item for item in service.locations if item.is_active), None)
        location_summary = None
        if location:
            location_summary = ", ".join(
                part for part in (location.city, location.region, location.service_area) if part
            )
        items.append(
            ServiceListItem(
                id=service.id,
                organization_name=service.organization.public_name,
                name=service.name,
                description=service.description,
                categories=[CategoryResponse.model_validate(item) for item in service.categories],
                location_summary=location_summary,
                languages=_split(service.languages),
                accessibility=service.accessibility,
                primary_contact=ContactResponse.model_validate(primary, from_attributes=True)
                if primary
                else None,
                verification=_verification(service),
            )
        )
    return ServiceListResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size),
        ),
    )


async def get_service(session: AsyncSession, service_id: UUID) -> ServiceResponse | None:
    service = await session.scalar(
        _base_public_query().where(Service.id == service_id).options(*_options())
    )
    if service is None:
        return None
    return ServiceResponse(
        id=service.id,
        organization=_organization(service.organization),
        name=service.name,
        description=service.description,
        eligibility=service.eligibility,
        required_documents=service.required_documents,
        cost_information=service.cost_information,
        languages=_split(service.languages),
        accessibility=service.accessibility,
        application_instructions=service.application_instructions,
        appointment_requirements=service.appointment_requirements,
        emergency_availability=service.emergency_availability,
        categories=[CategoryResponse.model_validate(item) for item in service.categories],
        locations=[
            LocationResponse.model_validate(item, from_attributes=True)
            for item in service.locations
        ],
        contacts=[
            ContactResponse.model_validate(item, from_attributes=True) for item in service.contacts
        ],
        sources=[
            SourceResponse.model_validate(item, from_attributes=True) for item in service.sources
        ],
        verification=_verification(service),
    )


async def create_draft(
    session: AsyncSession, organization: Organization, service: Service
) -> Service:
    """Internal boundary for future authenticated administration; no public route calls it."""
    service.organization = organization
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def transition_verification(
    session: AsyncSession, verification: Verification, target: VerificationStatus
) -> None:
    allowed = {
        VerificationStatus.DRAFT: {VerificationStatus.PENDING_REVIEW},
        VerificationStatus.PENDING_REVIEW: {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
        },
        VerificationStatus.VERIFIED: {
            VerificationStatus.NEEDS_REVERIFICATION,
            VerificationStatus.ARCHIVED,
        },
        VerificationStatus.NEEDS_REVERIFICATION: {
            VerificationStatus.VERIFIED,
            VerificationStatus.ARCHIVED,
        },
        VerificationStatus.REJECTED: {VerificationStatus.DRAFT},
        VerificationStatus.ARCHIVED: set(),
    }
    if target not in allowed[verification.status]:
        raise ValueError(f"Invalid verification transition: {verification.status} -> {target}")
    verification.status = target
    await session.commit()
