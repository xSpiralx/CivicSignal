import argparse
import asyncio
import getpass
import json
from datetime import datetime

from sqlalchemy import select

from civicsignal_api.core.config import get_settings
from civicsignal_api.db.session import create_database_engine, create_session_factory
from civicsignal_api.models.auth import AdminAccount, AuditEvent, Role, RoleName
from civicsignal_api.security import hash_password, normalize_identifier
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
    args = parser.parse_args()
    if args.command == "admin" and args.admin_command == "create":
        asyncio.run(create_admin(args.email, args.display_name))
    elif args.command == "resources" and args.resource_command == "detect-stale":
        asyncio.run(run_stale_detection(dry_run=args.dry_run, at=args.at))
