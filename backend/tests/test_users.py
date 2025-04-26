import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.auth import get_password_hash
from app.config import settings

# Create a test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_database():
    # Clean up database before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_register_user():
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "password" not in data

def test_register_duplicate_user():
    # First registration
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    client.post("/users/", json=user_data)
    
    # Try to register same user again
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "User already exists" in response.json()["detail"]

def test_login_user():
    # First register a user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    client.post("/users/", json=user_data)
    
    # Then try to login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_login_invalid_credentials():
    login_data = {
        "username": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_current_user():
    # First get a valid token
    token = test_login_user()
    
    # Then try to get current user
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "full_name" in data
    assert "id" in data
    return data["id"]

def test_get_user_by_id():
    # First get a valid token and user ID
    token = test_login_user()
    user_id = test_get_current_user()
    
    # Then try to get user by ID
    response = client.get(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert "email" in data
    assert "full_name" in data

def test_update_user():
    # First get a valid token and user ID
    token = test_login_user()
    user_id = test_get_current_user()
    
    # Then try to update user
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = client.put(
        f"/users/{user_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]

def test_delete_user():
    # First get a valid token and user ID
    token = test_login_user()
    user_id = test_get_current_user()
    
    # Then try to delete user
    response = client.delete(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    
    # Verify user is deleted
    response = client.get(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404 