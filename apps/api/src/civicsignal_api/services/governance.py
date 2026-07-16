from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.models.auth import AdminAccount, AuditEvent
from civicsignal_api.models.governance import (
    GovernanceDecision,
    GovernedResource,
    ResourceRevision,
    WorkflowState,
)
from civicsignal_api.models.resource import (
    Category,
    ContactChannel,
    ContactType,
    Location,
    Organization,
    Service,
    Source,
    SourceType,
    Verification,
    VerificationStatus,
)
from civicsignal_api.schemas.governance import DraftContent
from civicsignal_api.security import utcnow

TRANSITIONS: dict[tuple[WorkflowState, str], WorkflowState] = {
    (WorkflowState.DRAFT, "submit"): WorkflowState.SUBMITTED,
    (WorkflowState.CHANGES_REQUESTED, "submit"): WorkflowState.SUBMITTED,
    (WorkflowState.SUBMITTED, "request_changes"): WorkflowState.CHANGES_REQUESTED,
    (WorkflowState.SUBMITTED, "reject"): WorkflowState.REJECTED,
    (WorkflowState.SUBMITTED, "advance"): WorkflowState.PENDING_VERIFICATION,
    (WorkflowState.PENDING_VERIFICATION, "verify"): WorkflowState.VERIFIED,
    (WorkflowState.PENDING_VERIFICATION, "reject"): WorkflowState.REJECTED,
    (WorkflowState.VERIFIED, "publish"): WorkflowState.PUBLISHED,
    (WorkflowState.PUBLISHED, "request_reverification"): WorkflowState.NEEDS_REVERIFICATION,
    (WorkflowState.NEEDS_REVERIFICATION, "verify"): WorkflowState.VERIFIED,
    (WorkflowState.PUBLISHED, "archive"): WorkflowState.ARCHIVED,
    (WorkflowState.NEEDS_REVERIFICATION, "archive"): WorkflowState.ARCHIVED,
}


async def current_revision(db: AsyncSession, resource: GovernedResource) -> ResourceRevision:
    revision = await db.get(ResourceRevision, resource.current_revision_id)
    if revision is None:
        raise HTTPException(500, "Resource revision is unavailable")
    return revision


async def transition(
    db: AsyncSession,
    resource: GovernedResource,
    actor: AdminAccount,
    action: str,
    expected_revision: int,
    reason: str | None,
    evidence: list[str],
    next_due_at: datetime | None,
) -> ResourceRevision:
    revision = await current_revision(db, resource)
    if revision.number != expected_revision:
        raise HTTPException(409, "Resource changed; reload before continuing")
    target = TRANSITIONS.get((resource.state, action))
    if target is None:
        raise HTTPException(409, f"Cannot {action} a resource in {resource.state.value} state")
    if action in {"request_changes", "reject", "archive"} and not reason:
        raise HTTPException(422, "A reason is required")
    if action == "verify" and (not evidence or next_due_at is None):
        raise HTTPException(422, "Verification evidence and next due date are required")
    previous = resource.state
    resource.state = target
    if action == "verify":
        db.add(
            GovernanceDecision(
                resource_id=resource.id,
                revision_id=revision.id,
                actor_id=actor.id,
                action=action,
                reason=reason,
                evidence={"sources": evidence},
                next_due_at=next_due_at,
            )
        )
    else:
        db.add(
            GovernanceDecision(
                resource_id=resource.id,
                revision_id=revision.id,
                actor_id=actor.id,
                action=action,
                reason=reason,
            )
        )
    if action == "publish":
        await publish(db, resource, revision, actor, next_due_at)
    db.add(
        AuditEvent(
            actor_id=actor.id,
            action=f"resource.{action}",
            subject_type="governed_resource",
            subject_id=str(resource.id),
            summary=f"{previous.value} -> {target.value}",
        )
    )
    await db.commit()
    return revision


async def publish(
    db: AsyncSession,
    resource: GovernedResource,
    revision: ResourceRevision,
    actor: AdminAccount,
    next_due_at: datetime | None,
) -> None:
    content = DraftContent.model_validate(revision.content)
    if resource.public_service_id is None:
        organization = Organization(
            public_name=content.organization_name,
            legal_name=None,
            description=content.organization_description,
            organization_type=content.organization_type,
            website=str(content.website) if content.website else None,
            public_phone=content.contact_phone,
            public_email=content.contact_email,
            languages=", ".join(content.languages),
            accessibility=content.accessibility,
            is_active=True,
        )
        service = Service(
            organization=organization,
            name=content.service_name,
            description=content.description,
            eligibility=content.eligibility,
            required_documents=None,
            cost_information=None,
            languages=", ".join(content.languages),
            accessibility=content.accessibility,
            application_instructions=content.application_instructions,
            appointment_requirements=None,
            emergency_availability=content.emergency_availability,
            is_active=True,
        )
        db.add(service)
        await db.flush()
        resource.public_service_id = service.id
    else:
        existing_service = await db.get(Service, resource.public_service_id)
        if existing_service is None:
            raise HTTPException(500, "Published service is unavailable")
        service = existing_service
        service.name, service.description, service.eligibility = (
            content.service_name,
            content.description,
            content.eligibility,
        )
        service.languages, service.accessibility = (
            ", ".join(content.languages),
            content.accessibility,
        )
    for name in content.categories:
        slug = "-".join(name.casefold().split())[:80]
        category = await db.scalar(select(Category).where(Category.slug == slug))
        if category is None:
            category = Category(slug=slug, name=name[:120], description=None, is_active=True)
            db.add(category)
        service.categories.append(category)
    if content.location_name or content.service_area:
        db.add(
            Location(
                organization=service.organization,
                service=service,
                display_name=content.location_name or "Service area",
                address_line_1=None,
                address_line_2=None,
                city=content.city,
                region=content.region,
                postal_code=content.postal_code,
                country="US",
                latitude=None,
                longitude=None,
                service_area=content.service_area,
                transportation=content.transportation,
                accessibility=content.accessibility,
                hours=content.hours,
                timezone="America/New_York",
                is_active=True,
            )
        )
    for channel_type, label, value in (
        (ContactType.PHONE, "Phone", content.contact_phone),
        (ContactType.EMAIL, "Email", content.contact_email),
        (ContactType.WEBSITE, "Website", str(content.website) if content.website else None),
    ):
        if value:
            db.add(
                ContactChannel(
                    service=service,
                    channel_type=channel_type,
                    label=label,
                    value=value,
                    is_primary=channel_type == ContactType.PHONE,
                )
            )
    now = utcnow()
    db.add(
        Source(
            service_id=service.id,
            name=content.source_name,
            url=str(content.source_url),
            organization=content.source_organization,
            source_type=SourceType.PROVIDER_SUBMISSION,
            retrieved_at=now,
            last_checked_at=now,
            content_hash=None,
        )
    )
    db.add(
        Verification(
            service_id=service.id,
            status=VerificationStatus.VERIFIED,
            checked_at=now,
            expires_at=next_due_at or now + timedelta(days=90),
            checked_by=actor.display_name,
            notes="Published through governed workflow",
        )
    )
    resource.published_revision_id = revision.id
