from fastapi.testclient import TestClient
from unittest.mock import Mock
from app.main import app
from app.routers.journal import create_journal
from app.models.journal import Journal, JournalIn, JournalOut
from app.models.user import User, UserIn, UserOut

client = TestClient(app)

def test_mock_create_journal():
    mock_session = Mock()
    input = JournalIn(title="Post Mock-Test Title", body="Post Mock-Test Body")
    user = UserIn(username="test_user", password="123")
    result = create_journal(session=mock_session, user=user, new_journal=input)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert isinstance(result, Journal)
    assert result.title == "Post Mock-Test Title"
    assert result.body == "Post Mock-Test Body"

def test_create_journal():
    response = client.post("/api/journal/create",
                            json={"title":"Post Test Title", "body":"Post Test Body"}, 
                            auth=("test_user", "123"))
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"] == "Post Test Title"
    assert journal["body"] == "Post Test Body"

def test_delete_journal():
    pass

def test_replace_journal():
    pass

def test_get_journal():
    response = client.get("/api/journal/1")
    assert response.status_code == 200
    journal = response.json()
    assert journal["title"]
    assert journal["body"]