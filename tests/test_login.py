
from fastapi.testclient import TestClient
from app.core.config import settings

def test_login_success(client: TestClient):
    login_data = {
        "username": "admin@example.com",
        "password": "admin123",
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

def test_login_incorrect_password(client: TestClient):
    login_data = {
        "username": "admin@example.com",
        "password": "wrong_password",
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password",
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]
