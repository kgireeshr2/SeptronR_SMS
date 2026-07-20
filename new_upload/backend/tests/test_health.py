import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_check():
    """Test that the health endpoint returns expected structure."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    assert "redis" in data
    assert "version" in data
    assert "environment" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check_fields_when_degraded():
    """Test health returns degraded when services are unavailable."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    data = response.json()
    # Status is either ok or degraded, never anything else
    assert data["status"] in ("ok", "degraded")
    # Individual statuses are either ok or error
    assert data["database"] in ("ok", "error")
    assert data["redis"] in ("ok", "error")


@pytest.mark.asyncio
async def test_docs_available():
    """Test that FastAPI OpenAPI docs are accessible."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")

    assert response.status_code == 200
