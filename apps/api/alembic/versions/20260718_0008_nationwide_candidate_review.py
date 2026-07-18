"""Expand governed ingestion for nationwide candidate review."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260718_0008"
down_revision: str | None = "20260718_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    source_columns = (
        sa.Column("download_url", sa.String(2048)),
        sa.Column("jurisdiction", sa.String(240)),
        sa.Column("states_covered", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("localities_covered", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "redistribution_permitted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "modification_permitted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("latest_source_update_at", sa.DateTime(timezone=True)),
        sa.Column("latest_successful_retrieval_at", sa.DateTime(timezone=True)),
        sa.Column("freshness_policy", sa.Text()),
    )
    for column in source_columns:
        op.add_column("approved_sources", column)

    batch_columns = (
        sa.Column("idempotency_key", sa.String(160)),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checkpoint_row", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resume_token", sa.String(160)),
        sa.Column(
            "cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    for column in batch_columns:
        op.add_column("import_batches", column)
    op.execute(
        "UPDATE import_batches SET idempotency_key = "
        "CAST(source_id AS VARCHAR) || ':' || content_hash"
    )
    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.alter_column("idempotency_key", nullable=False)
    op.create_index(
        "ix_import_batches_idempotency_key", "import_batches", ["idempotency_key"], unique=True
    )
    op.create_index(
        "ix_import_batches_resume_token", "import_batches", ["resume_token"], unique=True
    )

    candidate_columns = (
        sa.Column("raw_content", sa.JSON()),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_content_hash", sa.String(64)),
        sa.Column("source_record_updated_at", sa.DateTime(timezone=True)),
        sa.Column("dataset_updated_at", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("city", sa.String(120)),
        sa.Column("county", sa.String(160)),
        sa.Column("region", sa.String(120)),
        sa.Column("postal_code", sa.String(30)),
        sa.Column("categories", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("service_area_type", sa.String(40), nullable=False, server_default="local"),
        sa.Column("nationwide", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("remote", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("risk_classification", sa.String(30), nullable=False, server_default="standard"),
        sa.Column("conflict_status", sa.String(50), nullable=False, server_default="none"),
        sa.Column("validation_status", sa.String(50), nullable=False, server_default="valid"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    for column in candidate_columns:
        op.add_column("candidate_resources", column)
    if dialect == "postgresql":
        op.execute(
            """UPDATE candidate_resources SET
            source_content_hash = normalized_fingerprint,
            retrieved_at = created_at,
            city = content->>'city', county = content->>'service_area',
            region = content->>'region', postal_code = content->>'postal_code',
            categories = COALESCE(content->'categories', '[]'::json),
            remote = COALESCE((content->>'remote_service_available')::boolean, false),
            review_status = CASE WHEN review_status = 'pending'
                THEN 'ready_for_review' ELSE review_status END
            """
        )
    else:
        op.execute(
            """UPDATE candidate_resources SET
            source_content_hash = normalized_fingerprint, retrieved_at = created_at,
            city = json_extract(content, '$.city'),
            county = json_extract(content, '$.service_area'),
            region = json_extract(content, '$.region'),
            postal_code = json_extract(content, '$.postal_code'),
            categories = COALESCE(json_extract(content, '$.categories'), '[]'),
            remote = COALESCE(json_extract(content, '$.remote_service_available'), 0),
            review_status = CASE WHEN review_status = 'pending'
                THEN 'ready_for_review' ELSE review_status END
            """
        )
    with op.batch_alter_table("candidate_resources") as batch_op:
        batch_op.alter_column("source_content_hash", nullable=False)
        batch_op.alter_column("retrieved_at", nullable=False)
    for column in (
        "source_content_hash",
        "source_record_updated_at",
        "dataset_updated_at",
        "retrieved_at",
        "city",
        "county",
        "region",
        "postal_code",
        "service_area_type",
        "nationwide",
        "remote",
        "risk_classification",
        "conflict_status",
        "validation_status",
    ):
        op.create_index(f"ix_candidate_resources_{column}", "candidate_resources", [column])
    op.create_index(
        "ix_candidate_review_queue",
        "candidate_resources",
        ["review_status", "risk_classification", "region", "city", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_review_queue", table_name="candidate_resources")
    for column in (
        "validation_status",
        "conflict_status",
        "risk_classification",
        "remote",
        "nationwide",
        "service_area_type",
        "postal_code",
        "region",
        "county",
        "city",
        "retrieved_at",
        "dataset_updated_at",
        "source_record_updated_at",
        "source_content_hash",
    ):
        op.drop_index(f"ix_candidate_resources_{column}", table_name="candidate_resources")
    for column in (
        "version",
        "validation_status",
        "conflict_status",
        "risk_classification",
        "remote",
        "nationwide",
        "service_area_type",
        "categories",
        "postal_code",
        "region",
        "county",
        "city",
        "retrieved_at",
        "dataset_updated_at",
        "source_record_updated_at",
        "source_content_hash",
        "source_url",
        "raw_content",
    ):
        op.drop_column("candidate_resources", column)
    op.drop_index("ix_import_batches_resume_token", table_name="import_batches")
    op.drop_index("ix_import_batches_idempotency_key", table_name="import_batches")
    for column in (
        "completed_at",
        "started_at",
        "cancellation_requested",
        "resume_token",
        "checkpoint_row",
        "failed_count",
        "processed_count",
        "idempotency_key",
    ):
        op.drop_column("import_batches", column)
    for column in (
        "freshness_policy",
        "latest_successful_retrieval_at",
        "latest_source_update_at",
        "modification_permitted",
        "redistribution_permitted",
        "localities_covered",
        "states_covered",
        "jurisdiction",
        "download_url",
    ):
        op.drop_column("approved_sources", column)
