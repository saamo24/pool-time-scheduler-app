
#!/usr/bin/env python3
"""
Test script for the Pool Time Scheduler API.
This script tests the main functionality of the API.

Usage:
  1. Make sure the API is running
  2. Run this script
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_V1 = "/api/v1"

def test_api():
    print("Testing Pool Time Scheduler API...")
    
    # Test the root endpoint
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    print("✅ Root endpoint OK")
    
    # Test authentication
    login_data = {
        "username": "admin@example.com",
        "password": "admin123",
    }
    response = requests.post(f"{BASE_URL}{API_V1}/login/access-token", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    
    admin_token = token_data["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Admin authentication OK")
    
    # Test visitor registration
    register_data = {
        "email": "new_visitor@example.com",
        "full_name": "New Visitor",
        "password": "visitor123",
        "gender": "male"
    }
    response = requests.post(f"{BASE_URL}{API_V1}/users/register", json=register_data)
    assert response.status_code == 200
    new_visitor = response.json()
    assert new_visitor["email"] == register_data["email"]
    assert new_visitor["role"] == "visitor"
    print("✅ Visitor registration OK")
    
    # Login as the new visitor
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"],
    }
    response = requests.post(f"{BASE_URL}{API_V1}/login/access-token", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    
    visitor_token = token_data["access_token"]
    visitor_headers = {"Authorization": f"Bearer {visitor_token}"}
    print("✅ Visitor authentication OK")
    
    # Test creating a group as admin
    now = datetime.now()
    group_data = {
        "name": "API Test Group",
        "description": "Group created by API test",
        "capacity": 15,
        "max_male": 8,
        "max_female": 7,
        "start_time": (now + timedelta(days=2)).isoformat(),
        "end_time": (now + timedelta(days=2, hours=2)).isoformat()
    }
    
    response = requests.post(f"{BASE_URL}{API_V1}/groups/", headers=admin_headers, json=group_data)
    assert response.status_code == 200
    group = response.json()
    assert group["name"] == group_data["name"]
    group_id = group["id"]
    print("✅ Group creation OK")
    
    # Test getting available groups as visitor
    response = requests.get(f"{BASE_URL}{API_V1}/groups/available", headers=visitor_headers)
    assert response.status_code == 200
    available_groups = response.json()
    # Group should be available since we just created it
    assert any(g["id"] == group_id for g in available_groups)
    print("✅ Getting available groups OK")
    
    # Test registering for a group as visitor
    registration_data = {
        "group_id": group_id,
        "attended": False
    }
    
    response = requests.post(f"{BASE_URL}{API_V1}/registrations/", headers=visitor_headers, json=registration_data)
    assert response.status_code == 200
    registration = response.json()
    assert registration["group_id"] == group_id
    print("✅ Group registration OK")
    
    # Test getting instructor availability for the group
    response = requests.get(
        f"{BASE_URL}{API_V1}/groups/{group_id}/available-instructors?sort_by=hours_scheduled", 
        headers=admin_headers
    )
    assert response.status_code == 200
    available_instructors = response.json()
    print("✅ Instructor availability check OK")
    
    # If there are instructors, assign one to the group
    if available_instructors:
        instructor_id = available_instructors[0]["instructor_id"]
        response = requests.put(
            f"{BASE_URL}{API_V1}/groups/{group_id}/instructor/{instructor_id}", 
            headers=admin_headers
        )
        assert response.status_code == 200
        updated_group = response.json()
        assert updated_group["instructor_id"] == instructor_id
        print("✅ Instructor assignment OK")
    
    # Test viewing registrations as visitor
    response = requests.get(f"{BASE_URL}{API_V1}/registrations/", headers=visitor_headers)
    assert response.status_code == 200
    visitor_registrations = response.json()
    assert len(visitor_registrations) > 0
    assert any(r["group_id"] == group_id for r in visitor_registrations)
    print("✅ Viewing registrations OK")
    
    print("\nAll tests passed successfully! The API is working correctly.")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"❌ Test failed: {e}")
