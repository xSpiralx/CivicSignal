from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, current_auth
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AdminAccount, AdminSession, AuditEvent
from civicsignal_api.policy import permissions_for
from civicsignal_api.schemas.auth import AccountView, SessionView, SignInRequest
from civicsignal_api.security import (
    as_utc,
    new_secret,
    normalize_identifier,
    secret_hash,
    utcnow,
    verify_password,
)

router = APIRouter(prefix="/api/v1/admin/auth", tags=["administrator authentication"])
GENERIC_FAILURE = "Invalid sign-in credentials"
Database = Annotated[AsyncSession, Depends(get_session)]
CurrentAuth = Annotated[AuthContext, Depends(current_auth)]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]


def view(auth: AuthContext, csrf_token: str) -> SessionView:
    account = auth.account
    return SessionView(
        account=AccountView(
            id=account.id,
            email=account.email,
            display_name=account.display_name,
            roles=sorted(role.name.value for role in account.roles),
            permissions=sorted(p.value for p in permissions_for(account)),
            is_active=account.is_active,
            created_at=account.created_at,
            last_login_at=account.last_login_at,
        ),
        csrf_token=csrf_token,
        expires_at=auth.session.expires_at,
        session_id=auth.session.id,
        created_at=auth.session.created_at,
    )


@router.post("/sign-in", response_model=SessionView)
async def sign_in(
    payload: SignInRequest, request: Request, response: Response, db: Database
) -> SessionView:
    result = await db.execute(
        select(AdminAccount)
        .options(selectinload(AdminAccount.roles))
        .where(AdminAccount.email == normalize_identifier(payload.email))
    )
    account = result.scalar_one_or_none()
    now = utcnow()
    valid, replacement = verify_password(
        account.password_hash if account else None, payload.password
    )
    if (
        not account
        or not valid
        or not account.is_active
        or (account.cooldown_until and as_utc(account.cooldown_until) > now)
    ):
        if account:
            account.failed_login_count += 1
            if account.failed_login_count >= 5:
                account.cooldown_until = now + timedelta(
                    minutes=min(account.failed_login_count - 4, 15)
                )
            await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, GENERIC_FAILURE)
    token, csrf = new_secret(), new_secret()
    session = AdminSession(
        account=account,
        token_hash=secret_hash(token),
        csrf_hash=secret_hash(csrf),
        last_used_at=now,
        expires_at=now + timedelta(seconds=request.app.state.settings.session_absolute_seconds),
    )
    account.failed_login_count = 0
    account.cooldown_until = None
    account.last_login_at = now
    if replacement:
        account.password_hash = replacement
    db.add_all(
        [
            session,
            AuditEvent(
                actor_id=account.id,
                action="auth.sign_in",
                subject_type="session",
                subject_id=str(session.id),
                summary="Administrator signed in",
            ),
        ]
    )
    await db.commit()
    await db.refresh(session)
    response.set_cookie(
        request.app.state.settings.session_cookie_name,
        token,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/api/v1/admin",
        max_age=request.app.state.settings.session_absolute_seconds,
    )
    return view(AuthContext(account, session), csrf)


@router.get("/session", response_model=SessionView)
async def current_session(db: Database, auth: CurrentAuth) -> SessionView:
    csrf = new_secret()
    auth.session.csrf_hash = secret_hash(csrf)
    await db.commit()
    return view(auth, csrf)


@router.post("/sign-out", status_code=204)
async def sign_out(request: Request, response: Response, db: Database, auth: CsrfAuth) -> None:
    auth.session.revoked_at = utcnow()
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="auth.sign_out",
            subject_type="session",
            subject_id=str(auth.session.id),
            summary="Administrator signed out",
        )
    )
    await db.commit()
    response.delete_cookie(request.app.state.settings.session_cookie_name, path="/api/v1/admin")
