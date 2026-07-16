import asyncio
import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from civicsignal_api.core.config import get_settings
from civicsignal_api.db.session import create_database_engine, create_session_factory
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

CATEGORIES = [
    ("emergency-shelter", "Emergency shelter"),
    ("food-assistance", "Food assistance"),
    ("housing-assistance", "Housing assistance"),
    ("utility-assistance", "Utility assistance"),
    ("transportation", "Transportation"),
    ("healthcare-access", "Healthcare access"),
    ("mental-health", "Mental health resources"),
    ("domestic-violence", "Domestic violence support"),
    ("child-family", "Child and family services"),
    ("disability-services", "Disability services"),
    ("legal-assistance", "Legal assistance"),
    ("employment-assistance", "Employment assistance"),
    ("disaster-recovery", "Disaster recovery"),
    ("cooling-center", "Cooling center"),
    ("warming-center", "Warming center"),
    ("government-alerts", "Government alerts"),
]
ORG_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
SERVICE_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")


async def seed() -> None:
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    async with factory() as session:
        for slug, name in CATEGORIES:
            if not await session.scalar(select(Category).where(Category.slug == slug)):
                session.add(
                    Category(
                        slug=slug,
                        name=name,
                        description=f"Services related to {name.lower()}.",
                        is_active=True,
                    )
                )
        if not await session.get(Organization, ORG_ID):
            organization = Organization(
                id=ORG_ID,
                public_name="Example Community Support Collaborative (Demonstration Only)",
                legal_name=None,
                description="A fictional organization used only to demonstrate CivicSignal.",
                organization_type="fictional demonstration",
                website="https://community-support.example",
                public_phone="+1-202-555-0100",
                public_email="help@community-support.example",
                languages="English, Spanish",
                accessibility="Wheelchair-accessible demonstration location.",
                is_active=True,
            )
            category = await session.scalar(
                select(Category).where(Category.slug == "food-assistance")
            )
            service = Service(
                id=SERVICE_ID,
                organization=organization,
                name="Example Food Support Program (Demonstration Only)",
                description="Fictional food-support listing for local demonstrations and tests.",
                eligibility="Demonstration text only; no real eligibility is represented.",
                required_documents="None in this fictional example.",
                cost_information="No cost in this fictional example.",
                languages="English, Spanish",
                accessibility="Wheelchair-accessible entrance in this fictional example.",
                application_instructions="Contact the fictional provider.",
                appointment_requirements="No appointment in this fictional example.",
                emergency_availability=False,
                is_active=True,
            )
            if category:
                service.categories.append(category)
            service.locations.append(
                Location(
                    organization=organization,
                    display_name="Example Community Center (Demonstration Only)",
                    address_line_1="100 Example Avenue",
                    city="Exampleville",
                    region="EX",
                    postal_code="00000",
                    country="US",
                    service_area="Example County",
                    transportation="Fictional bus route.",
                    accessibility="Wheelchair accessible.",
                    hours="Monday–Friday, 9:00–17:00 (demonstration only)",
                    timezone="America/New_York",
                    is_active=True,
                )
            )
            service.contacts.append(
                ContactChannel(
                    channel_type=ContactType.PHONE,
                    label="Demonstration phone",
                    value="+1-202-555-0100",
                    is_primary=True,
                )
            )
            now = datetime.now(UTC)
            service.sources.append(
                Source(
                    name="CivicSignal fictional demonstration dataset",
                    url="https://community-support.example/source",
                    organization="CivicSignal demonstration tooling",
                    source_type=SourceType.DEMONSTRATION,
                    retrieved_at=now,
                    last_checked_at=now,
                    content_hash=hashlib.sha256(b"civicsignal-demo-v1").hexdigest(),
                )
            )
            service.verifications.append(
                Verification(
                    status=VerificationStatus.VERIFIED,
                    checked_at=now,
                    expires_at=now + timedelta(days=30),
                    checked_by="CivicSignal demo seed",
                    notes="Fictional demonstration record; not a real public service.",
                )
            )
            session.add(organization)
        await session.commit()
    await engine.dispose()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
