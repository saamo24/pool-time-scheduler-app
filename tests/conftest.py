
import pytest
from typing import Generator, Dict

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import get_password_hash
from app.models.user import User, UserRole, Gender
from app.models.group import Group
from datetime import datetime, timedelta

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator:
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for the test
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Add test data
    try:
        # Create admin user
        admin_user = User(
            id=1,
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            gender=Gender.MALE,
        )
        session.add(admin_user)
        
        # Create instructor user
        instructor_user = User(
            id=2,
            email="instructor@example.com",
            hashed_password=get_password_hash("instructor123"),
            full_name="Instructor User",
            role=UserRole.INSTRUCTOR,
            gender=Gender.FEMALE,
        )
        session.add(instructor_user)
        
        # Create visitor user
        visitor_user = User(
            id=3,
            email="visitor@example.com",
            hashed_password=get_password_hash("visitor123"),
            full_name="Visitor User",
            role=UserRole.VISITOR,
            gender=Gender.MALE,
        )
        session.add(visitor_user)
        
        # Create a group
        now = datetime.now()
        group = Group(
            id=1,
            name="Test Group",
            description="Test group description",
            capacity=10,
            max_male=5,
            max_female=5,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            instructor_id=2,
        )
        session.add(group)
        
        session.commit()
        
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        
        # Drop the tables after the test is done
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db) -> Generator:
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Reset the dependency override
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def admin_token(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "admin@example.com",
        "password": "admin123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.fixture(scope="function")
def instructor_token(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "instructor@example.com",
        "password": "instructor123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.fixture(scope="function")
def visitor_token(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "visitor@example.com",
        "password": "visitor123",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}
