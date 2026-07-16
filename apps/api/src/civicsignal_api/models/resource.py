import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from civicsignal_api.db.base import Base


class VerificationStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    NEEDS_REVERIFICATION = "needs_reverification"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ContactType(str, enum.Enum):
    PHONE = "phone"
    TEXT = "text"
    EMAIL = "email"
    WEBSITE = "website"
    IN_PERSON = "in_person"
    HOTLINE = "hotline"
    RELAY = "relay_service"


class SourceType(str, enum.Enum):
    OFFICIAL_WEBSITE = "official_website"
    GOVERNMENT_DATASET = "government_dataset"
    PROVIDER_SUBMISSION = "provider_submission"
    DEMONSTRATION = "demonstration"


service_categories = Table(
    "service_categories",
    Base.metadata,
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (Index("ix_organizations_public_name", "public_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    public_name: Mapped[str] = mapped_column(String(200))
    legal_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    organization_type: Mapped[str] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(2048))
    public_phone: Mapped[str | None] = mapped_column(String(50))
    public_email: Mapped[str | None] = mapped_column(String(320))
    languages: Mapped[str] = mapped_column(Text, default="")
    accessibility: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    services: Mapped[list["Service"]] = relationship(back_populates="organization")
    locations: Mapped[list["Location"]] = relationship(back_populates="organization")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    __table_args__ = (Index("ix_services_name", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    eligibility: Mapped[str | None] = mapped_column(Text)
    required_documents: Mapped[str | None] = mapped_column(Text)
    cost_information: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[str] = mapped_column(Text, default="")
    accessibility: Mapped[str | None] = mapped_column(Text)
    application_instructions: Mapped[str | None] = mapped_column(Text)
    appointment_requirements: Mapped[str | None] = mapped_column(Text)
    emergency_availability: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    organization: Mapped[Organization] = relationship(back_populates="services")
    categories: Mapped[list[Category]] = relationship(secondary=service_categories)
    locations: Mapped[list["Location"]] = relationship(back_populates="service")
    contacts: Mapped[list["ContactChannel"]] = relationship(back_populates="service")
    sources: Mapped[list["Source"]] = relationship(back_populates="service")
    verifications: Mapped[list["Verification"]] = relationship(
        back_populates="service", order_by="Verification.checked_at"
    )


class Location(TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name="longitude_range"
        ),
        Index("ix_locations_region", "city", "region", "postal_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(200))
    address_line_1: Mapped[str | None] = mapped_column(String(200))
    address_line_2: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(30))
    country: Mapped[str] = mapped_column(String(2), default="US")
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    service_area: Mapped[str | None] = mapped_column(Text)
    transportation: Mapped[str | None] = mapped_column(Text)
    accessibility: Mapped[str | None] = mapped_column(Text)
    hours: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(100), default="America/New_York")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization: Mapped[Organization] = relationship(back_populates="locations")
    service: Mapped[Service | None] = relationship(back_populates="locations")


class ContactChannel(TimestampMixin, Base):
    __tablename__ = "contact_channels"
    __table_args__ = (CheckConstraint("length(value) > 0", name="contact_value_not_empty"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    channel_type: Mapped[ContactType] = mapped_column(Enum(ContactType, native_enum=False))
    label: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(2048))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    service: Mapped[Service] = relationship(back_populates="contacts")


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2048))
    organization: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, native_enum=False))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    service: Mapped[Service] = relationship(back_populates="sources")


class Verification(Base):
    __tablename__ = "verifications"
    __table_args__ = (Index("ix_verifications_public_state", "status", "checked_at"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False), index=True
    )
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_by: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    service: Mapped[Service] = relationship(back_populates="verifications")
