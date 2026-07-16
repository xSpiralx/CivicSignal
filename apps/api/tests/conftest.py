from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from civicsignal_api.app import create_app
from civicsignal_api.core.config import Settings
from civicsignal_api.db.base import Base


@pytest.fixture
def app() -> FastAPI:
    return create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        async with app.state.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as test_client:
            yield test_client
