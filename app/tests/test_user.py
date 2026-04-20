from httpx import AsyncClient, ASGITransport
from app.main import app
import pytest

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
async def create_test_user(client):
    response = await client.post("/api/user/create", json={"username":"test_user", "password":"123"})
    assert response.status_code == 201
    user = response.json()
    yield user["id"]
    await client.delete(f"/api/user/{user['id']}", auth=("default_user", "123"))

async def test_get_user(client, create_test_user):
    response = await client.get(f"/api/user/{create_test_user}")
    assert response.status_code == 200
    user = response.json()
    assert user["username"]
    assert user["id"]