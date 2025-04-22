
from fastapi.testclient import TestClient
from app.core.config import settings

def test_visitor_registration(client: TestClient, visitor_token):
    # Register for the group
    registration_data = {
        "group_id": 1,
        "attended": False
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/registrations/",
        headers=visitor_token,
        json=registration_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["group_id"] == 1
    assert data["visitor_id"] == 3  # visitor user has id 3
    
    # Check that the user can fetch their registrations
    response = client.get(
        f"{settings.API_V1_STR}/registrations/",
        headers=visitor_token
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["group_id"] == 1

def test_visitor_cannot_register_twice(client: TestClient, visitor_token):
    # Register for the group first time
    registration_data = {
        "group_id": 1,
        "attended": False
    }
    
    client.post(
        f"{settings.API_V1_STR}/registrations/",
        headers=visitor_token,
        json=registration_data
    )
    
    # Try to register again
    response = client.post(
        f"{settings.API_V1_STR}/registrations/",
        headers=visitor_token,
        json=registration_data
    )
    
    # Should still return 200 since we're returning the existing registration
    assert response.status_code == 200
    
    # Make sure there's still only one registration
    response = client.get(
        f"{settings.API_V1_STR}/registrations/",
        headers=visitor_token
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
