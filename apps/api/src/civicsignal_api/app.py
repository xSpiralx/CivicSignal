from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from civicsignal_api.core.config import Settings, get_settings
from civicsignal_api.core.errors import register_error_handlers
from civicsignal_api.core.logging import configure_logging
from civicsignal_api.core.middleware import correlation_id_middleware, request_size_middleware
from civicsignal_api.db.session import create_database_engine, create_session_factory
from civicsignal_api.routes.admin_accounts import router as admin_accounts_router
from civicsignal_api.routes.auth import router as auth_router
from civicsignal_api.routes.governance import router as governance_router
from civicsignal_api.routes.health import router as health_router
from civicsignal_api.routes.resources import router as resources_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(resolved_settings.database_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        description="Read-only public API for sourced community-resource records.",
    )
    app.state.settings = resolved_settings
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=resolved_settings.trusted_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
    )
    app.middleware("http")(request_size_middleware)
    app.middleware("http")(correlation_id_middleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_accounts_router)
    app.include_router(governance_router)
    app.include_router(resources_router)
    return app
