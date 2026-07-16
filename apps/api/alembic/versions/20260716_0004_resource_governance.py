"""Add versioned governed resource lifecycle."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0004"
down_revision: str | None = "20260716_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "governed_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column("current_revision_id", sa.Uuid()),
        sa.Column("published_revision_id", sa.Uuid()),
        sa.Column("public_service_id", sa.Uuid(), sa.ForeignKey("services.id"), unique=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id"), nullable=False),
        sa.Column("assigned_reviewer_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_governed_resources_state", "governed_resources", ["state"])
    op.create_index("ix_governed_resources_owner_id", "governed_resources", ["owner_id"])
    op.create_index(
        "ix_governed_resources_assigned_reviewer_id", "governed_resources", ["assigned_reviewer_id"]
    )
    op.create_table(
        "resource_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_id",
            sa.Uuid(),
            sa.ForeignKey("governed_resources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("resource_id", "number"),
    )
    op.create_index("ix_resource_revisions_resource_id", "resource_revisions", ["resource_id"])
    op.create_table(
        "governance_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("resource_id", sa.Uuid(), sa.ForeignKey("governed_resources.id"), nullable=False),
        sa.Column("revision_id", sa.Uuid(), sa.ForeignKey("resource_revisions.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("admin_accounts.id"), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("evidence", sa.JSON()),
        sa.Column("next_due_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_governance_decisions_resource_id", "governance_decisions", ["resource_id"])


def downgrade() -> None:
    op.drop_table("governance_decisions")
    op.drop_table("resource_revisions")
    op.drop_table("governed_resources")
