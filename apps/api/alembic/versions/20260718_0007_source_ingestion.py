"""Add governed source registry and draft-only ingestion records."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260718_0007"
down_revision: str | None = "20260718_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approved_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("stable_identifier", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("publishing_organization", sa.String(240), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("geographic_scope", sa.String(240), nullable=False),
        sa.Column("resource_categories", sa.JSON(), nullable=False),
        sa.Column("license_name", sa.String(240)),
        sa.Column("license_url", sa.String(2048)),
        sa.Column("terms_url", sa.String(2048)),
        sa.Column("attribution_requirement", sa.Text()),
        sa.Column("automation_permission", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("rate_limit", sa.String(240)),
        sa.Column("allowed_hosts", sa.JSON(), nullable=False),
        sa.Column("last_legal_review_at", sa.DateTime(timezone=True)),
        sa.Column("last_technical_review_at", sa.DateTime(timezone=True)),
        sa.Column("approval_status", sa.String(30), server_default="proposed", nullable=False),
        sa.Column(
            "reviewer_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id", ondelete="SET NULL")
        ),
        sa.Column("notes", sa.Text()),
        sa.Column("enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("import_method", sa.String(80), server_default="manual", nullable=False),
        sa.Column(
            "reliability_classification", sa.String(80), server_default="unassessed", nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_approved_sources_stable_identifier",
        "approved_sources",
        ["stable_identifier"],
        unique=True,
    )
    op.create_index("ix_approved_sources_approval_status", "approved_sources", ["approval_status"])
    op.create_index("ix_approved_sources_reviewer_id", "approved_sources", ["reviewer_id"])
    op.create_index("ix_approved_sources_enabled", "approved_sources", ["enabled"])

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("approved_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("license_snapshot", sa.Text()),
        sa.Column("attribution_snapshot", sa.Text()),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("importer_version", sa.String(40), nullable=False),
        sa.Column("original_filename", sa.String(240)),
        sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("accepted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("validation_result", sa.JSON(), nullable=False),
        sa.Column("review_decision", sa.Text()),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    for column in ("source_id", "status", "content_hash", "created_by_id"):
        op.create_index(f"ix_import_batches_{column}", "import_batches", [column])

    op.create_table(
        "candidate_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("approved_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_identifier", sa.String(240), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("normalized_fingerprint", sa.String(64), nullable=False),
        sa.Column("duplicate_classification", sa.String(50), nullable=False),
        sa.Column("validation_result", sa.JSON(), nullable=False),
        sa.Column("review_status", sa.String(40), server_default="pending", nullable=False),
        sa.Column("review_decision", sa.Text()),
        sa.Column(
            "reviewer_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id", ondelete="SET NULL")
        ),
        sa.Column(
            "governed_resource_id",
            sa.Uuid(),
            sa.ForeignKey("governed_resources.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("source_id", "source_identifier"),
    )
    for column in (
        "batch_id",
        "source_id",
        "normalized_fingerprint",
        "duplicate_classification",
        "review_status",
        "reviewer_id",
        "governed_resource_id",
    ):
        op.create_index(f"ix_candidate_resources_{column}", "candidate_resources", [column])


def downgrade() -> None:
    op.drop_table("candidate_resources")
    op.drop_table("import_batches")
    op.drop_table("approved_sources")
