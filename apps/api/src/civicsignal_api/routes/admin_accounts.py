import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AdminAccount, AdminSession, AuditEvent, Role, RoleName
from civicsignal_api.policy import Permission, permissions_for
from civicsignal_api.schemas.auth import (
    AccountCreate,
    AccountUpdate,
    AccountView,
    PasswordReplace,
    SafeSessionView,
)
from civicsignal_api.security import hash_password, normalize_identifier, utcnow

router = APIRouter(prefix="/api/v1/admin", tags=["administrator accounts"])
Database = Annotated[AsyncSession, Depends(get_session)]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]


AccountViewer = Annotated[AuthContext, Depends(require(Permission.ACCOUNT_VIEW))]
AccountCreator = Annotated[AuthContext, Depends(require(Permission.ACCOUNT_CREATE))]
AccountUpdater = Annotated[AuthContext, Depends(require(Permission.ACCOUNT_UPDATE))]
AdminManager = Annotated[AuthContext, Depends(require(Permission.ADMIN_MANAGE))]
SessionViewer = Annotated[AuthContext, Depends(require(Permission.SESSION_VIEW_ALL))]
SessionRevoker = Annotated[AuthContext, Depends(require(Permission.SESSION_REVOKE_ALL))]
CurrentAuth = Annotated[AuthContext, Depends(require(Permission.RESOURCE_VIEW))]


def account_view(account: AdminAccount) -> AccountView:
    return AccountView(
        id=account.id,
        email=account.email,
        display_name=account.display_name,
        roles=sorted(role.name.value for role in account.roles),
        permissions=sorted(item.value for item in permissions_for(account)),
        is_active=account.is_active,
        created_at=account.created_at,
        last_login_at=account.last_login_at,
    )


async def load_account(db: AsyncSession, account_id: uuid.UUID) -> AdminAccount:
    account = await db.scalar(
        select(AdminAccount)
        .options(selectinload(AdminAccount.roles))
        .where(AdminAccount.id == account_id)
    )
    if account is None:
        raise HTTPException(404, "Account not found")
    return account


async def roles_from_names(db: AsyncSession, names: list[str]) -> list[Role]:
    try:
        normalized = {RoleName(name) for name in names}
    except ValueError as exc:
        raise HTTPException(422, "Unknown role") from exc
    roles = list(await db.scalars(select(Role).where(Role.name.in_(normalized))))
    if len(roles) != len(normalized):
        raise HTTPException(422, "Unknown role")
    return roles


async def protect_last_admin(
    db: AsyncSession, account: AdminAccount, new_active: bool, roles: list[Role]
) -> None:
    was_admin = account.is_active and any(r.name == RoleName.ADMINISTRATOR for r in account.roles)
    remains_admin = new_active and any(r.name == RoleName.ADMINISTRATOR for r in roles)
    if was_admin and not remains_admin:
        count = await db.scalar(
            select(func.count(AdminAccount.id))
            .join(AdminAccount.roles)
            .where(AdminAccount.is_active, Role.name == RoleName.ADMINISTRATOR)
        )
        if count == 1:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Cannot remove the last active administrator"
            )


@router.get("/roles")
async def list_roles(db: Database, auth: AccountViewer) -> list[dict[str, object]]:
    roles = list(await db.scalars(select(Role).order_by(Role.id)))
    from civicsignal_api.policy import ROLE_PERMISSIONS

    return [
        {
            "name": role.name.value,
            "permissions": sorted(p.value for p in ROLE_PERMISSIONS[role.name]),
        }
        for role in roles
    ]


@router.get("/accounts", response_model=list[AccountView])
async def list_accounts(
    db: Database,
    auth: AccountViewer,
    q: Annotated[str | None, Query(max_length=120)] = None,
    active: bool | None = None,
) -> list[AccountView]:
    query = (
        select(AdminAccount)
        .options(selectinload(AdminAccount.roles))
        .order_by(AdminAccount.display_name)
        .limit(100)
    )
    if q:
        query = query.where(
            or_(AdminAccount.email.ilike(f"%{q}%"), AdminAccount.display_name.ilike(f"%{q}%"))
        )
    if active is not None:
        query = query.where(AdminAccount.is_active == active)
    return [account_view(item) for item in await db.scalars(query)]


@router.get("/accounts/{account_id}", response_model=AccountView)
async def get_account(account_id: uuid.UUID, db: Database, auth: AccountViewer) -> AccountView:
    return account_view(await load_account(db, account_id))


@router.post("/accounts", response_model=AccountView, status_code=201)
async def create_account(
    payload: AccountCreate,
    request: Request,
    db: Database,
    csrf: CsrfAuth,
    auth: AccountCreator,
) -> AccountView:
    email = normalize_identifier(payload.email)
    if await db.scalar(select(AdminAccount.id).where(AdminAccount.email == email)):
        raise HTTPException(409, "Account identifier already exists")
    account = AdminAccount(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        roles=await roles_from_names(db, payload.roles),
    )
    db.add(account)
    await db.flush()
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="account.create",
            subject_type="admin_account",
            subject_id=str(account.id),
            summary=f"Account created with roles: {', '.join(sorted(payload.roles))}",
        )
    )
    await db.commit()
    return account_view(account)


@router.patch("/accounts/{account_id}", response_model=AccountView)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    db: Database,
    csrf: CsrfAuth,
    auth: AccountUpdater,
) -> AccountView:
    account = await load_account(db, account_id)
    new_roles = (
        account.roles if payload.roles is None else await roles_from_names(db, payload.roles)
    )
    new_active = account.is_active if payload.is_active is None else payload.is_active
    await protect_last_admin(db, account, new_active, new_roles)
    if account.id == auth.account.id and Permission.ADMIN_MANAGE not in permissions_for(
        auth.account
    ):
        raise HTTPException(403, "Self-administration is not permitted")
    previous = f"active={account.is_active},roles={','.join(r.name.value for r in account.roles)}"
    if payload.display_name is not None:
        account.display_name = payload.display_name.strip()
    account.is_active = new_active
    account.roles = new_roles
    if payload.roles is not None or payload.is_active is False:
        await db.execute(
            update(AdminSession)
            .where(AdminSession.account_id == account.id, AdminSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="account.update",
            subject_type="admin_account",
            subject_id=str(account.id),
            summary=(
                f"{previous} -> active={new_active},"
                f"roles={','.join(r.name.value for r in new_roles)}"
            ),
        )
    )
    await db.commit()
    return account_view(account)


@router.post("/accounts/{account_id}/password", status_code=204)
async def replace_password(
    account_id: uuid.UUID,
    payload: PasswordReplace,
    db: Database,
    csrf: CsrfAuth,
    auth: AdminManager,
) -> None:
    account = await load_account(db, account_id)
    account.password_hash = hash_password(payload.password)
    account.password_changed_at = utcnow()
    await db.execute(
        update(AdminSession)
        .where(AdminSession.account_id == account.id, AdminSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="account.password_replace",
            subject_type="admin_account",
            subject_id=str(account.id),
            summary="Account password replaced and sessions revoked",
        )
    )
    await db.commit()


@router.get("/accounts/{account_id}/sessions", response_model=list[SafeSessionView])
async def account_sessions(
    account_id: uuid.UUID, db: Database, auth: SessionViewer
) -> list[SafeSessionView]:
    sessions = list(
        await db.scalars(
            select(AdminSession)
            .where(AdminSession.account_id == account_id, AdminSession.revoked_at.is_(None))
            .order_by(AdminSession.created_at.desc())
        )
    )
    return [
        SafeSessionView(
            id=s.id,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            expires_at=s.expires_at,
            current=s.id == auth.session.id,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: uuid.UUID,
    db: Database,
    csrf: CsrfAuth,
    auth: CurrentAuth,
) -> None:
    session = await db.get(AdminSession, session_id)
    if session is None or session.revoked_at is not None:
        raise HTTPException(409, "Session is already revoked or unavailable")
    if (
        session.account_id != auth.account.id
        and Permission.SESSION_REVOKE_ALL not in permissions_for(auth.account)
    ):
        raise HTTPException(403, "Permission denied")
    session.revoked_at = utcnow()
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="session.revoke",
            subject_type="admin_session",
            subject_id=str(session.id),
            summary="Selected session revoked",
        )
    )
    await db.commit()


@router.delete("/accounts/{account_id}/sessions", status_code=204)
async def revoke_all_sessions(
    account_id: uuid.UUID,
    db: Database,
    csrf: CsrfAuth,
    auth: SessionRevoker,
) -> None:
    await load_account(db, account_id)
    await db.execute(
        update(AdminSession)
        .where(AdminSession.account_id == account_id, AdminSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="session.revoke_all",
            subject_type="admin_account",
            subject_id=str(account_id),
            summary="All account sessions revoked",
        )
    )
    await db.commit()


@router.get("/sessions", response_model=list[SafeSessionView])
async def personal_sessions(
    db: Database, auth: Annotated[AuthContext, Depends(require(Permission.RESOURCE_VIEW))]
) -> list[SafeSessionView]:
    sessions = list(
        await db.scalars(
            select(AdminSession)
            .where(AdminSession.account_id == auth.account.id, AdminSession.revoked_at.is_(None))
            .order_by(AdminSession.created_at.desc())
        )
    )
    return [
        SafeSessionView(
            id=s.id,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            expires_at=s.expires_at,
            current=s.id == auth.session.id,
        )
        for s in sessions
    ]
