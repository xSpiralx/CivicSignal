import hmac
import logging
import time
from collections import Counter
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("civicsignal.request")
request_metrics: Counter[str] = Counter()


async def correlation_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied[:128] if supplied and supplied.isascii() else str(uuid4())
    request.state.request_id = request_id
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    request_metrics["requests_total"] += 1
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        request_metrics[f"responses_{response.status_code // 100}xx"] += 1
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response
    finally:
        request_id_context.reset(token)


async def request_size_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    content_length = request.headers.get("content-length")
    maximum = request.app.state.settings.max_request_bytes
    if content_length and (not content_length.isdigit() or int(content_length) > maximum):
        return JSONResponse(
            status_code=413,
            content={
                "error": {"code": "request_too_large", "message": "Request body too large"},
                "request_id": getattr(request.state, "request_id", None),
            },
        )
    return await call_next(request)


async def controlled_proxy_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    expected = request.app.state.settings.proxy_shared_secret
    if expected and request.url.path.startswith("/api/v1/"):
        supplied = request.headers.get("X-CivicSignal-Proxy", "")
        if not hmac.compare_digest(supplied, expected):
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "controlled_origin_required", "message": "Forbidden"}},
            )
    return await call_next(request)
