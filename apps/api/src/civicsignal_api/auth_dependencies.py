import secrets
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AdminAccount, AdminSession
from civicsignal_api.policy import Permission, permissions_for
from civicsignal_api.security import as_utc, secret_hash, utcnow

Database = Annotated[AsyncSession, Depends(get_session)]


@dataclass(frozen=True)
class AuthContext:
    account: AdminAccount
    session: AdminSession


async def current_auth(request: Request, db: Database) -> AuthContext:
    token = request.cookies.get(request.app.state.settings.session_cookie_name)
    if not token:
        raise HTTPException(401, "Authentication required")
    result = await db.execute(
        select(AdminSession)
        .options(selectinload(AdminSession.account).selectinload(AdminAccount.roles))
        .where(AdminSession.token_hash == secret_hash(token))
    )
    session = result.scalar_one_or_none()
    now = utcnow()
    if (
        not session
        or session.revoked_at
        or as_utc(session.expires_at) <= now
        or not session.account.is_active
        or as_utc(session.account.password_changed_at) > as_utc(session.created_at)
    ):
        raise HTTPException(401, "Authentication required")
    idle_seconds = request.app.state.settings.session_idle_seconds
    if (now - as_utc(session.last_used_at)).total_seconds() > idle_seconds:
        raise HTTPException(401, "Authentication required")
    session.last_used_at = now
    await db.commit()
    return AuthContext(session.account, session)


CurrentAuth = Annotated[AuthContext, Depends(current_auth)]


async def csrf_protected(request: Request, auth: CurrentAuth) -> AuthContext:
    supplied = request.headers.get("X-CSRF-Token", "")
    if not supplied or not secrets.compare_digest(secret_hash(supplied), auth.session.csrf_hash):
        raise HTTPException(403, "CSRF validation failed")
    return auth


def require(permission: Permission) -> Callable[[CurrentAuth], Coroutine[Any, Any, AuthContext]]:
    async def dependency(auth: CurrentAuth) -> AuthContext:
        if permission not in permissions_for(auth.account):
            raise HTTPException(403, "Permission denied")
        return auth

    return dependency
