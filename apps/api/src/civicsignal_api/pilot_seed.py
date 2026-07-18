import argparse
import asyncio
import hashlib
import json
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


class PilotLocation(TypedDict):
    name: str
    address: str | None
    postal_code: str | None
    hours: str | None
    accessibility: str | None


class PilotContact(TypedDict):
    type: ContactType
    label: str
    value: str


class PilotService(TypedDict):
    key: str
    organization: str
    name: str
    category: str
    description: str
    eligibility: str
    required_documents: str | None
    cost: str
    languages: str
    accessibility: str | None
    application: str
    appointments: str | None
    website: str
    sources: list[tuple[str, str]]
    contacts: list[PilotContact]
    locations: list[PilotLocation]


PILOT_SERVICES: list[PilotService] = [
    {
        "key": "dc-public-benefits-centers",
        "organization": "District of Columbia Department of Human Services",
        "name": "Public Benefits Service Centers",
        "category": "food-assistance",
        "description": (
            "In-person help applying for or managing District public benefits, including food, "
            "medical, and cash assistance."
        ),
        "eligibility": (
            "District of Columbia residents seeking public-benefit information. Program-specific "
            "eligibility is determined by DC DHS."
        ),
        "required_documents": "Requirements vary by program; confirm with DC DHS before visiting.",
        "cost": "No fee is listed for service-center assistance.",
        "languages": "English; request language assistance from DC DHS",
        "accessibility": "Call 711 for DC Relay or contact DC DHS for accommodations.",
        "application": "Visit an open service center or call the Public Benefits Call Center.",
        "appointments": "The official source describes in-person support; confirm current access.",
        "website": "https://dhs.dc.gov/service/find-service-center-near-you",
        "sources": [
            (
                "DC DHS — Find a Service Center Near You",
                "https://dhs.dc.gov/service/find-service-center-near-you",
            )
        ],
        "contacts": [
            {
                "type": ContactType.PHONE,
                "label": "Public Benefits Call Center",
                "value": "+1-202-727-5355",
            }
        ],
        "locations": [
            {
                "name": "Anacostia Service Center",
                "address": "2100 Martin Luther King Jr. Avenue SE",
                "postal_code": "20020",
                "hours": "Monday–Friday, 7:30 AM–4:45 PM",
                "accessibility": None,
            },
            {
                "name": "Fort Davis Service Center",
                "address": "3851 Alabama Avenue SE",
                "postal_code": "20020",
                "hours": "Monday–Friday, 7:30 AM–4:45 PM",
                "accessibility": None,
            },
            {
                "name": "Congress Heights Service Center",
                "address": "4049 South Capitol Street SW",
                "postal_code": "20032",
                "hours": "Monday–Friday, 7:30 AM–4:45 PM",
                "accessibility": None,
            },
            {
                "name": "H Street Service Center",
                "address": "645 H Street NE",
                "postal_code": "20002",
                "hours": "Monday–Friday, 7:30 AM–4:45 PM",
                "accessibility": None,
            },
            {
                "name": "Taylor Street Service Center",
                "address": "1207 Taylor Street NW",
                "postal_code": "20011",
                "hours": "Monday–Friday, 7:30 AM–4:45 PM",
                "accessibility": None,
            },
        ],
    },
    {
        "key": "dc-day-services-centers",
        "organization": "District of Columbia Department of Human Services",
        "name": "Day Services Centers",
        "category": "housing-assistance",
        "description": (
            "Daytime hygiene, laundry, device charging, case management, benefits, health, "
            "employment, and other supports for people experiencing homelessness."
        ),
        "eligibility": "Individuals experiencing homelessness in the District of Columbia.",
        "required_documents": "No universal document requirement is stated; confirm onsite.",
        "cost": "DC DHS describes these services as available through funded day centers.",
        "languages": "Contact the center or DC DHS to request language assistance",
        "accessibility": "Accessible transportation can be requested through the hotline.",
        "application": "Visit a listed center or call the Homeless Services Hotline for help.",
        "appointments": "Hours and entry can change; call before traveling.",
        "website": "https://dhs.dc.gov/page/day-services-centers",
        "sources": [
            ("DC DHS — Day Services Centers", "https://dhs.dc.gov/page/day-services-centers")
        ],
        "contacts": [
            {
                "type": ContactType.HOTLINE,
                "label": "Homeless Services Hotline",
                "value": "+1-202-399-7093",
            }
        ],
        "locations": [
            {
                "name": "Downtown Day Services Center",
                "address": "1313 New York Avenue NW",
                "postal_code": "20005",
                "hours": "Monday–Friday, 9 AM–5 PM; Saturday, 10 AM–3 PM",
                "accessibility": None,
            },
            {
                "name": "Adams Place Day Center",
                "address": "2210 Adams Place NE",
                "postal_code": "20018",
                "hours": "Monday–Friday, 9 AM–5 PM",
                "accessibility": None,
            },
            {
                "name": "801 East Day Center",
                "address": "2722 Martin Luther King Jr. Avenue SE",
                "postal_code": "20032",
                "hours": "Monday–Friday, 9 AM–5 PM",
                "accessibility": None,
            },
        ],
    },
    {
        "key": "dc-american-job-center",
        "organization": "District of Columbia Department of Employment Services",
        "name": "American Job Center Services",
        "category": "employment-assistance",
        "description": (
            "Workforce workshops, job-search support, and in-person American Job Center services."
        ),
        "eligibility": "Job seekers and workers; confirm program-specific eligibility with DOES.",
        "required_documents": "Requirements vary by service and appointment.",
        "cost": "No fee is listed on the official service page.",
        "languages": "Contact DOES to request language assistance",
        "accessibility": "Auxiliary aids and services are available upon request.",
        "application": "Use the official page for appointments or call the DOES call center.",
        "appointments": "The official page states in-person services are by appointment only.",
        "website": "https://does.dc.gov/service/american-job-center",
        "sources": [
            ("DC DOES — American Job Center", "https://does.dc.gov/service/american-job-center"),
            (
                "DC DOES — Contact Information",
                "https://unemployment.dc.gov/page/contact-information-1",
            ),
        ],
        "contacts": [
            {"type": ContactType.PHONE, "label": "DOES call center", "value": "+1-202-724-7000"}
        ],
        "locations": [
            {
                "name": "American Job Center Headquarters",
                "address": "4058 Minnesota Avenue NE",
                "postal_code": "20019",
                "hours": "Monday–Friday, 8:30 AM–4:30 PM; confirm before visiting",
                "accessibility": "Auxiliary aids and services available upon request.",
            }
        ],
    },
    {
        "key": "dc-dda-intake",
        "organization": "District of Columbia Department on Disability Services",
        "name": "Developmental Disabilities Administration Intake",
        "category": "disability-services",
        "description": (
            "Walk-in or scheduled intake and eligibility determination for developmental "
            "disability services."
        ),
        "eligibility": (
            "District residents seeking DDA services; the agency determines eligibility."
        ),
        "required_documents": (
            "The official application guidance lists residency, insurance, and supporting records; "
            "review the current checklist before applying."
        ),
        "cost": "No intake fee is listed on the official page.",
        "languages": "English; applications listed in Spanish, Korean, Vietnamese, Amharic, French",
        "accessibility": "TTY contact is available; request accommodations from DDS.",
        "application": (
            "Walk in or call to schedule an appointment; forms are on the official site."
        ),
        "appointments": "Walk-ins are accepted, or call to schedule.",
        "website": "https://dds.dc.gov/service/how-apply-services",
        "sources": [
            (
                "DC DDS — How to Apply for DDA Services",
                "https://dds.dc.gov/service/how-apply-services",
            )
        ],
        "contacts": [
            {"type": ContactType.PHONE, "label": "DDA intake", "value": "+1-202-730-1700"},
            {"type": ContactType.RELAY, "label": "TTY", "value": "+1-202-730-1516"},
        ],
        "locations": [
            {
                "name": "DDS/DDA Intake and Eligibility Determination Unit",
                "address": "250 E Street SW",
                "postal_code": "20024",
                "hours": "Monday–Friday, 8:30 AM–5 PM",
                "accessibility": "Contact DDS for accommodations; TTY is available.",
            }
        ],
    },
    {
        "key": "dc-snap",
        "organization": "District of Columbia Department of Human Services",
        "name": "Supplemental Nutrition Assistance Program (SNAP)",
        "category": "food-assistance",
        "description": "Monthly food-purchase benefits for eligible individuals and families.",
        "eligibility": (
            "Income and household rules apply. Federal work requirements changed in 2026; DC DHS "
            "makes the eligibility determination."
        ),
        "required_documents": "Application and verification requirements vary by household.",
        "cost": "No application fee is listed.",
        "languages": "Contact DC DHS to request language assistance",
        "accessibility": "Call 711 for DC Relay or contact DC DHS for accommodations.",
        "application": "Use the DC Benefits Portal, visit a DHS center, or call the benefits line.",
        "appointments": None,
        "website": "https://dhs.dc.gov/service/supplemental-nutrition-assistance-program-snap",
        "sources": [
            (
                "DC DHS — Supplemental Nutrition Assistance Program",
                "https://dhs.dc.gov/service/supplemental-nutrition-assistance-program-snap",
            )
        ],
        "contacts": [
            {
                "type": ContactType.PHONE,
                "label": "Public Benefits Call Center",
                "value": "+1-202-727-5355",
            }
        ],
        "locations": [
            {
                "name": "District-wide and online service",
                "address": None,
                "postal_code": None,
                "hours": "Confirm current portal and call-center availability with DC DHS",
                "accessibility": None,
            }
        ],
    },
]


async def seed_pilot(*, reviewer_name: str) -> tuple[int, int]:
    reviewer = reviewer_name.strip()
    if len(reviewer) < 3:
        raise ValueError("A named human reviewer is required")
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    inserted = 0
    existing = 0
    now = datetime.now(UTC)
    async with factory() as session:
        for item in PILOT_SERVICES:
            service_id = uuid.uuid5(uuid.NAMESPACE_URL, f"civicsignal-dc-pilot-{item['key']}")
            if await session.get(Service, service_id):
                existing += 1
                continue
            category = await session.scalar(
                select(Category).where(Category.slug == item["category"])
            )
            if category is None:
                raise RuntimeError("Run civicsignal-seed before loading pilot records")
            organization = Organization(
                id=uuid.uuid5(uuid.NAMESPACE_URL, f"civicsignal-dc-pilot-org-{item['key']}"),
                public_name=item["organization"],
                legal_name=item["organization"],
                description="District government organization serving Washington, DC.",
                organization_type="government",
                website=item["website"],
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
                required_documents=item["required_documents"],
                cost_information=item["cost"],
                languages=item["languages"],
                accessibility=item["accessibility"],
                application_instructions=item["application"],
                appointment_requirements=item["appointments"],
                emergency_availability=False,
                is_active=True,
            )
            service.categories.append(category)
            for location in item["locations"]:
                service.locations.append(
                    Location(
                        organization=organization,
                        display_name=location["name"],
                        address_line_1=location["address"],
                        city="Washington",
                        region="DC",
                        postal_code=location["postal_code"],
                        country="US",
                        service_area="District of Columbia",
                        accessibility=location["accessibility"],
                        hours=location["hours"],
                        timezone="America/New_York",
                        is_active=True,
                    )
                )
            for index, contact in enumerate(item["contacts"]):
                service.contacts.append(
                    ContactChannel(
                        channel_type=contact["type"],
                        label=contact["label"],
                        value=contact["value"],
                        is_primary=index == 0,
                    )
                )
            payload_hash = hashlib.sha256(
                json.dumps(item, default=str, sort_keys=True).encode()
            ).hexdigest()
            for source_name, source_url in item["sources"]:
                service.sources.append(
                    Source(
                        name=source_name,
                        url=source_url,
                        organization=item["organization"],
                        source_type=SourceType.OFFICIAL_WEBSITE,
                        retrieved_at=now,
                        last_checked_at=now,
                        content_hash=payload_hash,
                    )
                )
            service.verifications.append(
                Verification(
                    status=VerificationStatus.VERIFIED,
                    checked_at=now,
                    expires_at=now + timedelta(days=14),
                    checked_by=reviewer,
                    notes=(
                        "Limited Washington, DC pilot. Human reviewer acknowledged comparison "
                        "against every cited official source before publication."
                    ),
                )
            )
            session.add(organization)
            inserted += 1
        await session.commit()
    await engine.dispose()
    return inserted, existing


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the human-reviewed Washington, DC pilot")
    parser.add_argument("--reviewer-name", required=True)
    parser.add_argument("--acknowledge-source-review", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_source_review:
        parser.error(
            "--acknowledge-source-review is required after a human checks every cited source"
        )
    inserted, existing = asyncio.run(seed_pilot(reviewer_name=args.reviewer_name))
    print(json.dumps({"inserted": inserted, "existing": existing, "mode": "dc-pilot"}))


if __name__ == "__main__":
    main()
