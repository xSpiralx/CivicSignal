import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.db.dependencies import get_session
from civicsignal_api.services.stale_detection import detect_stale

router = APIRouter(prefix="/internal/maintenance", tags=["maintenance"])
Database = Annotated[AsyncSession, Depends(get_session)]


def authorize(request: Request, authorization: Annotated[str | None, Header()] = None) -> None:
    expected = request.app.state.settings.maintenance_token
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not expected or not hmac.compare_digest(supplied, expected):
        raise HTTPException(403, "Forbidden")


@router.post("/detect-stale", include_in_schema=False)
async def run_stale_detection(
    db: Database, authorization: Annotated[None, Depends(authorize)]
) -> dict[str, Any]:
    summary = await detect_stale(db, dry_run=False)
    return summary.as_dict()
