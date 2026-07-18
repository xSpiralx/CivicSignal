"""Add idempotent re-verification work queue."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0005"
down_revision: str | None = "20260716_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reverification_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resource_id", sa.Uuid(), sa.ForeignKey("governed_resources.id", ondelete="SET NULL")
        ),
        sa.Column("reason", sa.String(80), nullable=False),
        sa.Column("freshness_state", sa.String(30), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column(
            "assigned_verifier_id",
            sa.Uuid(),
            sa.ForeignKey("admin_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("service_id", "active", name="uq_active_reverification_per_service"),
    )
    for column in (
        "service_id",
        "resource_id",
        "freshness_state",
        "due_at",
        "active",
        "assigned_verifier_id",
    ):
        op.create_index(f"ix_reverification_tasks_{column}", "reverification_tasks", [column])


def downgrade() -> None:
    op.drop_table("reverification_tasks")
