from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, AsyncMock
from app.main import app
from app.routers.journal import create_journal
from app.routers.auth import hash_password
from app.models.journal import Journal, JournalIn, JournalOut
from app.models.user import User, UserIn, UserOut
import pytest

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

async def test_mock_create_journal():
    mock_session = AsyncMock()
    mock_session.add = Mock()
    input = JournalIn(title="Post Mock-Test Title", body="Post Mock-Test Body")
    user = User(username="test_user", password_hash=hash_password("123"), id="1", )
    result = await create_journal(session=mock_session, user=user, new_journal=input)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert isinstance(result, Journal)
    assert result.title == "Post Mock-Test Title"
    assert result.body == "Post Mock-Test Body"

@pytest.fixture
async def create_test_journal(client):
    response = await client.post("/api/journal/create",
                            json={"title":"Post Test Title", "body":"Post Test Body"}, 
                            auth=("default_user", "123"))
    assert response.status_code == 201
    journal = response.json()
    yield journal["id"]


async def test_delete_journal(client, create_test_journal):
    response = await client.delete(f"/api/journal/{create_test_journal}", auth=("default_user", "123"))
    assert response.status_code == 204

async def test_replace_journal(client, create_test_journal):
    response = await client.put(f"/api/journal/{create_test_journal}",
                            json={"title":"Update Test Title", "body":"Update Test Body"}, 
                            auth=("default_user", "123"))
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Update Test Title"
    assert journal["body"] == "Update Test Body"

async def test_update_journal(client, create_test_journal):
    response = await client.patch(f"/api/journal/{create_test_journal}",
                            json={"body":"Patch Test Body"}, 
                            auth=("default_user", "123"))
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Post Test Title"
    assert journal["body"] == "Patch Test Body"


    response = await client.patch(f"/api/journal/{create_test_journal}",
                            json={"title":"Patch Test Title"}, 
                            auth=("default_user", "123"))
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Patch Test Title"
    assert journal["body"] == "Patch Test Body"

async def test_get_journal(client, create_test_journal):
    response = await client.get(f"/api/journal/{create_test_journal}", auth=("default_user", "123"))
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"]
    assert journal["body"]