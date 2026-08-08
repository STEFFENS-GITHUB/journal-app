import os

import redis.asyncio as redis
from redis import Redis
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.models.user import User
from api.utils.utils import create_email_verification_token
from api.utils.database import create_db_engine
from api.utils.queue import create_sqs_client
import pytest

@pytest.fixture
async def client():
    if os.getenv("DATABASE_URL_LOCAL"):
        os.environ["DATABASE_URL"] = os.environ["DATABASE_URL_LOCAL"]
    if os.getenv("REDIS_URL_LOCAL"):
        os.environ["REDIS_URL"] = os.environ["REDIS_URL_LOCAL"]
    app.state.engine, app.state.session_factory = create_db_engine()
    app.state.sqs_client = create_sqs_client()
    app.state.redis_client = redis.from_url(os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()
    await app.state.redis_client.aclose()

@pytest.fixture(autouse=True)
def flush_rate_limits():
    url = os.getenv("REDIS_URL_LOCAL") or os.getenv("REDIS_URL")
    redis_client = Redis.from_url(url)
    for key in redis_client.scan_iter("ratelimit:*"):
        redis_client.delete(key)
    redis_client.close()

TEST_USERNAME = "test_user"
TEST_EMAIL = "test_user@example.com"
TEST_PASSWORD = "password123!"

async def delete_test_user(user_id):
    try:
        async with app.state.session_factory() as session:
            user = await session.get(User, user_id)
            if user:
                await session.delete(user)
                await session.commit()
    except Exception as e:
        print(f"teardown: could not delete user {user_id}: {e}")

@pytest.fixture
async def create_test_user(client):
    response = await client.post("/register", json={"username": TEST_USERNAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    user = response.json()
    token = create_email_verification_token(user["id"])
    response = await client.get(f"/verify-email?token={token}")
    assert response.status_code == 200
    response = await client.post("/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    yield user["id"], headers
    await delete_test_user(user["id"])

@pytest.fixture
async def auth_headers(client):
    response = await client.post("/login", data={
        "username": os.environ["DEFAULT_USER"],
        "password": os.environ["DEFAULT_USER_PASSWORD"],
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
