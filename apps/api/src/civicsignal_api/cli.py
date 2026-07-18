import argparse
import asyncio
import getpass
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from civicsignal_api.core.config import get_settings
from civicsignal_api.db.session import create_database_engine, create_session_factory
from civicsignal_api.models.auth import AdminAccount, AuditEvent, Role, RoleName
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
