"""Add verified resource directory tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0002"
down_revision: str | None = "20260716_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("public_name", sa.String(200), nullable=False),
        sa.Column("legal_name", sa.String(200)),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("organization_type", sa.String(100), nullable=False),
        sa.Column("website", sa.String(2048)),
        sa.Column("public_phone", sa.String(50)),
        sa.Column("public_email", sa.String(320)),
        sa.Column("languages", sa.Text(), nullable=False),
        sa.Column("accessibility", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_organizations_public_name", "organizations", ["public_name"])
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"])
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("eligibility", sa.Text()),
        sa.Column("required_documents", sa.Text()),
        sa.Column("cost_information", sa.Text()),
        sa.Column("languages", sa.Text(), nullable=False),
        sa.Column("accessibility", sa.Text()),
        sa.Column("application_instructions", sa.Text()),
        sa.Column("appointment_requirements", sa.Text()),
        sa.Column("emergency_availability", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_services_name", "services", ["name"])
    op.create_index("ix_services_organization_id", "services", ["organization_id"])
    op.create_index("ix_services_is_active", "services", ["is_active"])
    op.create_table(
        "service_categories",
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )
    op.create_table(
        "locations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="RESTRICT")),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("address_line_1", sa.String(200)),
        sa.Column("address_line_2", sa.String(200)),
        sa.Column("city", sa.String(120)),
        sa.Column("region", sa.String(120)),
        sa.Column("postal_code", sa.String(30)),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("service_area", sa.Text()),
        sa.Column("transportation", sa.Text()),
        sa.Column("accessibility", sa.Text()),
        sa.Column("hours", sa.Text()),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90", name="latitude_range"
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name="longitude_range"
        ),
    )
    op.create_index("ix_locations_region", "locations", ["city", "region", "postal_code"])
    op.create_index("ix_locations_organization_id", "locations", ["organization_id"])
    op.create_index("ix_locations_service_id", "locations", ["service_id"])
    op.create_table(
        "contact_channels",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("channel_type", sa.String(20), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("value", sa.String(2048), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("length(value) > 0", name="contact_value_not_empty"),
    )
    op.create_index("ix_contact_channels_service_id", "contact_channels", ["service_id"])
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("organization", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(128)),
        *timestamps(),
    )
    op.create_index("ix_sources_service_id", "sources", ["service_id"])
    op.create_index("ix_sources_last_checked_at", "sources", ["last_checked_at"])
    op.create_table(
        "verifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("checked_by", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text()),
    )
    op.create_index("ix_verifications_service_id", "verifications", ["service_id"])
    op.create_index("ix_verifications_status", "verifications", ["status"])
    op.create_index("ix_verifications_public_state", "verifications", ["status", "checked_at"])


def downgrade() -> None:
    for table in (
        "verifications",
        "sources",
        "contact_channels",
        "locations",
        "service_categories",
        "services",
        "categories",
        "organizations",
    ):
        op.drop_table(table)
