
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.core.config import settings
import json

def test_create_group(client: TestClient, admin_token):
    now = datetime.now()
    group_data = {
        "name": "New Test Group",
        "description": "A new test group",
        "capacity": 15,
        "max_male": 8,
        "max_female": 7,
        "start_time": (now + timedelta(days=2)).isoformat(),
        "end_time": (now + timedelta(days=2, hours=2)).isoformat(),
        "instructor_id": 2
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=admin_token,
        json=group_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == group_data["name"]
    assert data["capacity"] == group_data["capacity"]
    assert data["instructor_id"] == group_data["instructor_id"]

def test_get_group(client: TestClient, admin_token):
    response = client.get(
        f"{settings.API_V1_STR}/groups/1",
        headers=admin_token
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Group"
    assert data["instructor_id"] == 2

def test_unauthorized_create_group(client: TestClient, visitor_token):
    now = datetime.now()
    group_data = {
        "name": "Unauthorized Group",
        "description": "This should fail",
        "capacity": 10,
        "max_male": 5,
        "max_female": 5,
        "start_time": (now + timedelta(days=3)).isoformat(),
        "end_time": (now + timedelta(days=3, hours=1)).isoformat()
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=visitor_token,
        json=group_data
    )
    
    assert response.status_code == 403
    assert "Not enough privileges" in response.json()["detail"]
