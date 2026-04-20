from fastapi.testclient import TestClient

from app.main import app
client = TestClient(app)

def test_create_user():
    pass

def test_get_user():
    response = client.get("/api/user/1")
    assert response.status_code == 200
    user = response.json()
    assert user["username"]
    assert user["id"]