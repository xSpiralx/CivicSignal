import argparse
import asyncio
import getpass
import json
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from civicsignal_api.core.config import get_settings
from civicsignal_api.db.session import create_database_engine, create_session_factory
from civicsignal_api.models.auth import AdminAccount, AuditEvent, Role, RoleName
from civicsignal_api.models.ingestion import (
    ApprovedSource,
    CandidateResource,
    ImportBatch,
    SourceApprovalStatus,
)
from civicsignal_api.security import hash_password, normalize_identifier
from civicsignal_api.services.hrsa_2026 import prepare_hrsa_2026_snapshot
from civicsignal_api.services.ingestion import preview_or_import_file
from civicsignal_api.services.stale_detection import detect_stale


async def create_admin(email: str, display_name: str) -> None:
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match")
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as db:
            normalized = normalize_identifier(email)
            if await db.scalar(select(AdminAccount.id).where(AdminAccount.email == normalized)):
                raise SystemExit("Account already exists")
            role = await db.scalar(select(Role).where(Role.name == RoleName.ADMINISTRATOR))
            if role is None:
                raise SystemExit("Database migrations are not current")
            account = AdminAccount(
                email=normalized,
                display_name=display_name.strip(),
                password_hash=hash_password(password),
                roles=[role],
            )
            db.add(account)
            await db.flush()
            db.add(
                AuditEvent(
                    actor_id=account.id,
                    action="admin.bootstrap",
                    subject_type="admin_account",
                    subject_id=str(account.id),
                    summary="Initial administrator created by explicit CLI command",
                )
            )
            await db.commit()
    finally:
        await engine.dispose()
    print("Administrator created")


async def run_stale_detection(*, dry_run: bool, at: str | None) -> None:
    execution_time = datetime.fromisoformat(at.replace("Z", "+00:00")) if at else None
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as db:
            summary = await detect_stale(db, now=execution_time, dry_run=dry_run)
    finally:
        await engine.dispose()
    print(json.dumps(summary.as_dict(), sort_keys=True))


async def import_source_file(
    *, source: str, actor_email: str, path: str, media_type: str, commit: bool
) -> None:
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as db:
            actor = await db.scalar(
                select(AdminAccount).where(
                    AdminAccount.email == normalize_identifier(actor_email),
                    AdminAccount.is_active,
                )
            )
            if actor is None:
                raise SystemExit("Active import actor was not found")
            result = await preview_or_import_file(
                db,
                source_identifier=source,
                actor_id=actor.id,
                file_path=Path(path),
                media_type=media_type,
                commit=commit,
            )
    finally:
        await engine.dispose()
    print(json.dumps(result.as_dict(), sort_keys=True))


async def register_hrsa_source(actor_email: str) -> None:
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as db:
            actor = await db.scalar(
                select(AdminAccount).where(AdminAccount.email == normalize_identifier(actor_email))
            )
            if actor is None:
                raise SystemExit("Active source reviewer was not found")
            existing = await db.scalar(
                select(ApprovedSource).where(
                    ApprovedSource.stable_identifier == "hrsa-health-center-sites-2026"
                )
            )
            if existing:
                print(
                    json.dumps(
                        {
                            "source": existing.stable_identifier,
                            "status": existing.approval_status.value,
                            "created": False,
                        }
                    )
                )
                return
            reviewed = datetime.fromisoformat("2026-07-18T21:30:00+00:00")
            source_updated = datetime.fromisoformat("2026-07-16T00:00:00+00:00")
            source = ApprovedSource(
                stable_identifier="hrsa-health-center-sites-2026",
                name="Health Center Service Delivery and Look-Alike Sites",
                publishing_organization="U.S. Health Resources and Services Administration",
                source_url="https://data.hrsa.gov/data/download?titleFilter=Health+Center",
                download_url="https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv",
                source_type="federal_open_data",
                geographic_scope="United States and territories",
                jurisdiction="United States",
                states_covered=[],
                localities_covered=[],
                resource_categories=["Healthcare access"],
                license_name="U.S. Government open data; HRSA usage limitations: none",
                license_url="https://data.hrsa.gov/data/data-sources?tab=DataUsage",
                terms_url="https://data.hrsa.gov/data/data-sources?tab=DataUsage",
                attribution_requirement=(
                    "Attribute HRSA and link the official dataset landing page."
                ),
                redistribution_permitted=True,
                modification_permitted=True,
                automation_permission=True,
                rate_limit="Manual bounded snapshot import; no scheduled retrieval",
                allowed_hosts=["data.hrsa.gov"],
                last_legal_review_at=reviewed,
                last_technical_review_at=reviewed,
                latest_source_update_at=source_updated,
                freshness_policy=(
                    "Only active records with a trustworthy 2025 or 2026 record or dataset date."
                ),
                approval_status=SourceApprovalStatus.APPROVED,
                reviewer_id=actor.id,
                notes="Engineering/data-governance review completed; not formal legal advice.",
                enabled=True,
                import_method="bounded_manual_snapshot",
                reliability_classification="authoritative_identity_and_location",
            )
            db.add(source)
            await db.flush()
            db.add(
                AuditEvent(
                    actor_id=actor.id,
                    action="source.approved",
                    subject_type="approved_source",
                    subject_id=str(source.id),
                    summary="HRSA 2026 source approved for bounded, draft-only candidate import",
                )
            )
            await db.commit()
            print(
                json.dumps(
                    {"source": source.stable_identifier, "status": "approved", "created": True}
                )
            )
    finally:
        await engine.dispose()


async def list_source_registry() -> None:
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as db:
            rows = list(
                await db.scalars(select(ApprovedSource).order_by(ApprovedSource.stable_identifier))
            )
            print(
                json.dumps(
                    [
                        {
                            "id": str(item.id),
                            "source": item.stable_identifier,
                            "status": item.approval_status.value,
                            "enabled": item.enabled,
                        }
                        for item in rows
                    ],
                    sort_keys=True,
                )
            )
    finally:
        await engine.dispose()


async def import_summary(batch_id: str | None = None) -> None:
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    try:
        async with factory() as db:
            if batch_id:
                batch = await db.get(ImportBatch, uuid.UUID(batch_id))
                if batch is None:
                    raise SystemExit("Import batch not found")
                result = {
                    "batch_id": str(batch.id),
                    "status": batch.status.value,
                    "rows": batch.row_count,
                    "candidates": batch.accepted_count,
                    "rejected": batch.rejected_count,
                    "checkpoint_row": batch.checkpoint_row,
                }
            else:
                result = {
                    "batches": int(await db.scalar(select(func.count(ImportBatch.id))) or 0),
                    "candidates": int(
                        await db.scalar(select(func.count(CandidateResource.id))) or 0
                    ),
                    "published": 0,
                }
            print(json.dumps(result, sort_keys=True))
    finally:
        await engine.dispose()


def prepare_hrsa_source(
    *, input_path: str, output_dir: str, source_updated_at: str, retrieved_at: str
) -> None:
    result = prepare_hrsa_2026_snapshot(
        Path(input_path),
        Path(output_dir),
        source_updated_at=source_updated_at,
        retrieved_at=retrieved_at,
    )
    print(json.dumps(result.as_dict(), sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(prog="civicsignal")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("admin")
    admin_commands = admin.add_subparsers(dest="admin_command", required=True)
    create = admin_commands.add_parser("create")
    create.add_argument("--email", required=True)
    create.add_argument("--display-name", required=True)
    resources = commands.add_parser("resources")
    resource_commands = resources.add_subparsers(dest="resource_command", required=True)
    stale = resource_commands.add_parser("detect-stale")
    stale.add_argument("--dry-run", action="store_true")
    stale.add_argument("--at", help="ISO 8601 execution time for deterministic runs")
    sources = commands.add_parser("sources")
    source_commands = sources.add_subparsers(dest="source_command", required=True)
    source_import = source_commands.add_parser("import")
    source_import.add_argument("--source", required=True, help="Approved source identifier")
    source_import.add_argument("--actor-email", required=True)
    source_import.add_argument("--file", required=True)
    source_import.add_argument(
        "--media-type", required=True, choices=["text/csv", "application/json"]
    )
    source_import.add_argument(
        "--commit", action="store_true", help="Persist candidates; otherwise performs a dry run"
    )
    source_prepare_hrsa = source_commands.add_parser("prepare-hrsa-2026")
    source_prepare_hrsa.add_argument("--input", required=True, help="Official HRSA CSV snapshot")
    source_prepare_hrsa.add_argument(
        "--output", default="var/imports/hrsa-2026", help="Ignored review staging directory"
    )
    source_prepare_hrsa.add_argument("--source-updated-at", required=True)
    source_prepare_hrsa.add_argument("--retrieved-at", required=True)
    source_commands.add_parser("list")
    source_commands.add_parser("validate")
    source_register_hrsa = source_commands.add_parser("register-hrsa-2026")
    source_register_hrsa.add_argument("--actor-email", required=True)
    imports = commands.add_parser("imports")
    import_commands = imports.add_subparsers(dest="import_command", required=True)
    import_run = import_commands.add_parser("run")
    import_run.add_argument("--source", required=True)
    import_run.add_argument("--actor-email", required=True)
    import_run.add_argument("--file", required=True)
    import_run.add_argument(
        "--media-type", default="application/json", choices=["text/csv", "application/json"]
    )
    import_run.add_argument("--commit", action="store_true")
    import_status = import_commands.add_parser("status")
    import_status.add_argument("--batch", required=True)
    import_commands.add_parser("summarize")
    args = parser.parse_args()
    if args.command == "admin" and args.admin_command == "create":
        asyncio.run(create_admin(args.email, args.display_name))
    elif args.command == "resources" and args.resource_command == "detect-stale":
        asyncio.run(run_stale_detection(dry_run=args.dry_run, at=args.at))
    elif args.command == "sources" and args.source_command == "import":
        asyncio.run(
            import_source_file(
                source=args.source,
                actor_email=args.actor_email,
                path=args.file,
                media_type=args.media_type,
                commit=args.commit,
            )
        )
    elif args.command == "sources" and args.source_command == "prepare-hrsa-2026":
        prepare_hrsa_source(
            input_path=args.input,
            output_dir=args.output,
            source_updated_at=args.source_updated_at,
            retrieved_at=args.retrieved_at,
        )
    elif args.command == "sources" and args.source_command == "register-hrsa-2026":
        asyncio.run(register_hrsa_source(args.actor_email))
    elif args.command == "sources" and args.source_command in {"list", "validate"}:
        asyncio.run(list_source_registry())
    elif args.command == "imports" and args.import_command == "run":
        asyncio.run(
            import_source_file(
                source=args.source,
                actor_email=args.actor_email,
                path=args.file,
                media_type=args.media_type,
                commit=args.commit,
            )
        )
    elif args.command == "imports" and args.import_command == "status":
        asyncio.run(import_summary(args.batch))
    elif args.command == "imports" and args.import_command == "summarize":
        asyncio.run(import_summary())
