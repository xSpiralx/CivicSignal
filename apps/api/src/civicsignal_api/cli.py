import argparse
import asyncio
import getpass

from sqlalchemy import select

from civicsignal_api.core.config import get_settings
from civicsignal_api.db.session import create_database_engine, create_session_factory
from civicsignal_api.models.auth import AdminAccount, AuditEvent, Role, RoleName
from civicsignal_api.security import hash_password, normalize_identifier


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


def main() -> None:
    parser = argparse.ArgumentParser(prog="civicsignal")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("admin")
    admin_commands = admin.add_subparsers(dest="admin_command", required=True)
    create = admin_commands.add_parser("create")
    create.add_argument("--email", required=True)
    create.add_argument("--display-name", required=True)
    args = parser.parse_args()
    if args.command == "admin" and args.admin_command == "create":
        asyncio.run(create_admin(args.email, args.display_name))
