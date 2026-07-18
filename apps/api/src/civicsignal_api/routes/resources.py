from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.resource import Category
from civicsignal_api.schemas.resources import (
    CategoryResponse,
    OrganizationSummary,
    ServiceListResponse,
    ServiceResponse,
)
from civicsignal_api.services.resources import get_service, list_services

router = APIRouter(prefix="/api/v1", tags=["public resources"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/categories", response_model=list[CategoryResponse], summary="List active categories")
async def categories(session: Session) -> list[CategoryResponse]:
    rows = await session.scalars(select(Category).where(Category.is_active).order_by(Category.name))
    return [CategoryResponse.model_validate(item) for item in rows.all()]


@router.get("/services", response_model=ServiceListResponse, summary="Search public services")
@router.get("/search", response_model=ServiceListResponse, include_in_schema=False)
async def services(
    session: Session,
    q: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    state: Annotated[str | None, Query(max_length=120)] = None,
    postal_code: Annotated[str | None, Query(max_length=30)] = None,
    language: Annotated[str | None, Query(max_length=80)] = None,
    accessibility: Annotated[str | None, Query(max_length=120)] = None,
    eligibility: Annotated[str | None, Query(max_length=200)] = None,
    sort: Literal["name", "organization", "state_city", "recently_verified"] = "name",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> ServiceListResponse:
    return await list_services(
        session,
        query=q,
        category=category,
        city=city,
        region=state,
        postal_code=postal_code,
        language=language,
        accessibility=accessibility,
        eligibility=eligibility,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/services/{service_id}", response_model=ServiceResponse, summary="View a public service"
)
async def service_detail(service_id: UUID, session: Session) -> ServiceResponse:
    result = await get_service(session, service_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return result


@router.get("/organizations", response_model=list[OrganizationSummary])
async def organizations(session: Session) -> list[OrganizationSummary]:
    result = await list_services(
        session,
        query=None,
        category=None,
        city=None,
        region=None,
        postal_code=None,
        language=None,
        accessibility=None,
        eligibility=None,
        sort="name",
        page=1,
        page_size=50,
    )
    seen: set[UUID] = set()
    output: list[OrganizationSummary] = []
    for item in result.items:
        service = await get_service(session, item.id)
        if service and service.organization.id not in seen:
            seen.add(service.organization.id)
            output.append(service.organization)
    return output


@router.get("/organizations/{organization_id}", response_model=OrganizationSummary)
async def organization_detail(organization_id: UUID, session: Session) -> OrganizationSummary:
    for organization in await organizations(session):
        if organization.id == organization_id:
            return organization
    raise HTTPException(status_code=404, detail="Organization not found")
