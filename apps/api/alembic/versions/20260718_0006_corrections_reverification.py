"""Add correction reports and operational re-verification fields."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260718_0006"
down_revision: str | None = "20260716_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("reverification_tasks") as batch:
        batch.add_column(sa.Column("published_revision_id", sa.Uuid(), nullable=True))
        batch.add_column(
            sa.Column(
                "trigger_source", sa.String(40), server_default="stale_detection", nullable=False
            )
        )
        batch.add_column(sa.Column("status", sa.String(30), server_default="open", nullable=False))
        batch.add_column(sa.Column("version", sa.Integer(), server_default="1", nullable=False))
        batch.add_column(sa.Column("claimed_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("started_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("outcome", sa.String(40)))
        batch.add_column(sa.Column("evidence_summary", sa.Text()))
        batch.add_column(sa.Column("contact_attempt_summary", sa.Text()))
        batch.add_column(sa.Column("source_references", sa.JSON()))
        batch.add_column(sa.Column("notes", sa.Text()))
        batch.create_foreign_key(
            "fk_reverification_published_revision",
            "resource_revisions",
            ["published_revision_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_reverification_tasks_status", "reverification_tasks", ["status"])

    op.create_table(
        "correction_reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "published_revision_id",
            sa.Uuid(),
            sa.ForeignKey("resource_revisions.id", ondelete="SET NULL"),
        ),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reporter_name", sa.String(120)),
        sa.Column("reporter_email", sa.String(320)),
        sa.Column("content_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), server_default="new", nullable=False),
        sa.Column(
            "assigned_reviewer_id",
            sa.Uuid(),
            sa.ForeignKey("admin_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "duplicate_of_id",
            sa.Uuid(),
            sa.ForeignKey("correction_reports.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "task_id", sa.Uuid(), sa.ForeignKey("reverification_tasks.id", ondelete="SET NULL")
        ),
        sa.Column("resolution_reason", sa.Text()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "length(description) BETWEEN 10 AND 4000", name="correction_description_length"
        ),
    )
    for column in (
        "service_id",
        "category",
        "content_fingerprint",
        "status",
        "assigned_reviewer_id",
        "task_id",
        "submitted_at",
    ):
        op.create_index(f"ix_correction_reports_{column}", "correction_reports", [column])


def downgrade() -> None:
    op.drop_table("correction_reports")
    op.drop_index("ix_reverification_tasks_status", table_name="reverification_tasks")
    with op.batch_alter_table("reverification_tasks") as batch:
        batch.drop_constraint("fk_reverification_published_revision", type_="foreignkey")
        for column in (
            "notes",
            "source_references",
            "contact_attempt_summary",
            "evidence_summary",
            "outcome",
            "started_at",
            "claimed_at",
            "version",
            "status",
            "trigger_source",
            "published_revision_id",
        ):
            batch.drop_column(column)
