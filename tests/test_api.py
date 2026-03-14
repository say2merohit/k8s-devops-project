import pytest
from httpx import AsyncClient, ASGITransport
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_readiness(client):
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_info(client):
    response = await client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "fastapi-k8s-demo"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_get_item_valid(client):
    response = await client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["item_id"] == 1


@pytest.mark.asyncio
async def test_get_item_invalid(client):
    response = await client.get("/items/0")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_item_valid(client):
    response = await client.post("/items?name=Widget&price=9.99")
    assert response.status_code == 200
    assert response.json()["created"] is True


@pytest.mark.asyncio
async def test_create_item_negative_price(client):
    response = await client.post("/items?name=Widget&price=-1")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.content
