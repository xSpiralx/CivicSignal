import asyncio
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

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


class DemoService(TypedDict):
    key: str
    organization: str
    name: str
    category: str
    description: str
    eligibility: str
    languages: str
    accessibility: str
    area: str
    hours: str
    phone: str


DEMO_SERVICES: list[DemoService] = [
    {
        "key": "housing",
        "organization": "Harborlight Housing Network (Fictional)",
        "name": "Housing Navigation and Tenant Support (Fictional)",
        "category": "housing-assistance",
        "description": (
            "Fictional housing navigation, application guidance, and tenant-support referrals."
        ),
        "eligibility": "Example County residents seeking housing information.",
        "languages": "English, Spanish, Haitian Creole",
        "accessibility": (
            "Step-free office, accessible restroom, and video appointments by request."
        ),
        "area": "Example County",
        "hours": "Monday–Thursday, 8:30–16:30; Friday by appointment",
        "phone": "+1-202-555-0111",
    },
    {
        "key": "employment",
        "organization": "Northstar Work Collaborative (Fictional)",
        "name": "Career Coaching and Job Search Lab (Fictional)",
        "category": "employment-assistance",
        "description": (
            "Fictional résumé coaching, interview practice, and computer access for job searches."
        ),
        "eligibility": "Adults and transition-age youth; no referral required.",
        "languages": "English, Spanish",
        "accessibility": "Screen-reader workstations and adjustable-height desks are available.",
        "area": "Exampleville and surrounding towns",
        "hours": "Tuesday–Saturday, 10:00–18:00",
        "phone": "+1-202-555-0112",
    },
    {
        "key": "childcare",
        "organization": "Bright Path Family Exchange (Fictional)",
        "name": "Childcare Referral and Subsidy Guidance (Fictional)",
        "category": "child-family",
        "description": (
            "Fictional help comparing childcare options and understanding example "
            "subsidy applications."
        ),
        "eligibility": "Parents, guardians, and caregivers in the fictional service area.",
        "languages": "English, Spanish, Mandarin",
        "accessibility": (
            "Phone interpretation and sensory-friendly appointment times are available."
        ),
        "area": "Example County",
        "hours": "Monday–Friday, 9:00–17:30",
        "phone": "+1-202-555-0113",
    },
    {
        "key": "transportation",
        "organization": "Open Road Mobility Center (Fictional)",
        "name": "Accessible Transportation Planning (Fictional)",
        "category": "transportation",
        "description": (
            "Fictional trip planning and eligibility guidance for accessible community "
            "transportation."
        ),
        "eligibility": "Older adults and people with disabilities in Example County.",
        "languages": "English, ASL by appointment",
        "accessibility": (
            "Relay calls, ASL appointments, large-print materials, and step-free access."
        ),
        "area": "Example County",
        "hours": "Monday–Friday, 8:00–16:00",
        "phone": "+1-202-555-0114",
    },
    {
        "key": "remote-senior",
        "organization": "Neighborline Senior Connections (Fictional)",
        "name": "Remote Benefits and Technology Support (Fictional)",
        "category": "disability-services",
        "description": (
            "Fictional remote help with benefits forms, accessible devices, and video-call setup."
        ),
        "eligibility": "Older adults and adults with disabilities; remote service only.",
        "languages": "English, Spanish, Vietnamese",
        "accessibility": (
            "Relay service, captioned video, and plain-language materials are available."
        ),
        "area": "Statewide fictional remote service",
        "hours": "Monday–Friday, 10:00–19:00",
        "phone": "+1-202-555-0115",
    },
]


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
        now = datetime.now(UTC)
        for item in DEMO_SERVICES:
            organization_id = uuid.uuid5(uuid.NAMESPACE_URL, f"civicsignal-demo-org-{item['key']}")
            service_id = uuid.uuid5(uuid.NAMESPACE_URL, f"civicsignal-demo-service-{item['key']}")
            if await session.get(Service, service_id):
                continue
            organization = Organization(
                id=organization_id,
                public_name=item["organization"],
                legal_name=None,
                description=(
                    "A fictional organization created for the CivicSignal portfolio demonstration."
                ),
                organization_type="fictional demonstration",
                website=f"https://{item['key']}.example",
                public_phone=item["phone"],
                public_email=f"hello@{item['key']}.example",
                languages=item["languages"],
                accessibility=item["accessibility"],
                is_active=True,
            )
            service = Service(
                id=service_id,
                organization=organization,
                name=item["name"],
                description=item["description"],
                eligibility=item["eligibility"],
                required_documents="No documents required for this fictional demonstration.",
                cost_information="No cost in this fictional example.",
                languages=item["languages"],
                accessibility=item["accessibility"],
                application_instructions=(
                    "Call the fictional demonstration number or use the reserved .example website."
                ),
                appointment_requirements=(
                    "Appointments recommended but not required in this fictional example."
                ),
                emergency_availability=False,
                is_active=True,
            )
            category = await session.scalar(
                select(Category).where(Category.slug == item["category"])
            )
            if category:
                service.categories.append(category)
            organization_label = item["organization"].removesuffix(" Center (Fictional)")
            organization_label = organization_label.removesuffix(" (Fictional)")
            service.locations.append(
                Location(
                    organization=organization,
                    display_name=(
                        "Remote service (Fictional)"
                        if item["key"] == "remote-senior"
                        else f"{organization_label} Center (Fictional)"
                    ),
                    address_line_1=None if item["key"] == "remote-senior" else "200 Example Plaza",
                    city=None if item["key"] == "remote-senior" else "Exampleville",
                    region="EX",
                    postal_code=None if item["key"] == "remote-senior" else "00000",
                    country="US",
                    service_area=item["area"],
                    transportation="Contact the fictional provider for accessible travel options.",
                    accessibility=item["accessibility"],
                    hours=item["hours"],
                    timezone="America/New_York",
                    is_active=True,
                )
            )
            service.contacts.append(
                ContactChannel(
                    channel_type=ContactType.PHONE,
                    label="Demonstration phone",
                    value=item["phone"],
                    is_primary=True,
                )
            )
            service.sources.append(
                Source(
                    name="CivicSignal fictional portfolio dataset",
                    url=f"https://{item['key']}.example/source",
                    organization="CivicSignal demonstration tooling",
                    source_type=SourceType.DEMONSTRATION,
                    retrieved_at=now,
                    last_checked_at=now,
                    content_hash=hashlib.sha256(
                        f"civicsignal-{item['key']}-v1".encode()
                    ).hexdigest(),
                )
            )
            service.verifications.append(
                Verification(
                    status=VerificationStatus.VERIFIED,
                    checked_at=now,
                    expires_at=now + timedelta(days=30),
                    checked_by="CivicSignal portfolio seed",
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
