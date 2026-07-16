from httpx import AsyncClient


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


async def test_readiness_checks_database(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_correlation_id_is_preserved(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "test-request"})
    assert response.headers["X-Request-ID"] == "test-request"


async def test_errors_have_central_structure(client: AsyncClient) -> None:
    response = await client.get("/missing", headers={"X-Request-ID": "error-request"})
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "http_error", "message": "Not Found"},
        "request_id": "error-request",
    }
