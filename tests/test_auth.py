"""
Tests for authentication endpoints: register, login, refresh, and /me.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import app first to ensure all models are registered
from main import app
from app.db.database import Base, get_db

# In-memory SQLite for tests — StaticPool ensures all connections share the same DB
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable FK enforcement for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def teardown_module(module):
    """Clear dependency overrides after this module finishes."""
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and drop after."""
    # Import all models to make sure they're registered
    import app.models  # noqa
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestRegister:
    def test_register_success(self):
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "securepass123",
            "display_name": "Test User",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_register_duplicate_email(self):
        client.post("/api/v1/auth/register", json={
            "email": "dupe@example.com",
            "password": "securepass123",
            "display_name": "First User",
        })
        response = client.post("/api/v1/auth/register", json={
            "email": "dupe@example.com",
            "password": "anotherpass123",
            "display_name": "Second User",
        })
        assert response.status_code == 409

    def test_register_short_password(self):
        response = client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "123",
            "display_name": "Short Pass",
        })
        assert response.status_code == 422

    def test_register_missing_email(self):
        response = client.post("/api/v1/auth/register", json={
            "password": "securepass123",
            "display_name": "No Email",
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self):
        client.post("/api/v1/auth/register", json={
            "email": "login@example.com",
            "password": "mypassword123",
            "display_name": "Login User",
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "mypassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self):
        client.post("/api/v1/auth/register", json={
            "email": "wrongpw@example.com",
            "password": "correctpassword",
            "display_name": "Wrong PW",
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "whatever123",
        })
        assert response.status_code == 401


class TestTokenRefresh:
    def test_refresh_success(self):
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "refresh@example.com",
            "password": "refreshpass123",
            "display_name": "Refresh User",
        })
        refresh_token = reg_response.json()["refresh_token"]

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self):
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert response.status_code == 401

    def test_refresh_with_access_token_fails(self):
        """Using an access token for refresh should fail (wrong type claim)."""
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "noaccess@example.com",
            "password": "accesspass123",
            "display_name": "No Access",
        })
        access_token = reg_response.json()["access_token"]

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token,
        })
        assert response.status_code == 401


class TestMe:
    def test_get_me(self):
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "me@example.com",
            "password": "mepassword123",
            "display_name": "Me User",
        })
        access_token = reg_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["display_name"] == "Me User"
        assert data["is_active"] is True

    def test_get_me_no_token(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_update_me(self):
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "update@example.com",
            "password": "updatepass123",
            "display_name": "Old Name",
        })
        access_token = reg_response.json()["access_token"]

        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"display_name": "New Name"},
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "New Name"


class TestWorkspaces:
    def test_personal_workspace_created_on_register(self):
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "workspace@example.com",
            "password": "workspacepass123",
            "display_name": "Workspace User",
        })
        access_token = reg_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/workspaces",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "personal-" in data[0]["slug"]


class TestAuthenticatedItems:
    def test_create_item_authenticated(self):
        """Items created while authenticated should be owned by the user."""
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "items@example.com",
            "password": "itemspass123",
            "display_name": "Items User",
        })
        access_token = reg_response.json()["access_token"]

        response = client.post(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"title": "My Task", "description": "A personal task"},
        )
        assert response.status_code == 201
        assert response.json()["title"] == "My Task"

    def test_create_item_anonymous(self):
        """Items created without auth should still work (backwards compat)."""
        response = client.post(
            "/api/v1/items",
            json={"title": "Anonymous Task", "description": "No auth"},
        )
        assert response.status_code == 201

    def test_user_sees_only_own_items(self):
        """Authenticated user should only see their items + unowned items."""
        # Register user A
        reg_a = client.post("/api/v1/auth/register", json={
            "email": "usera@example.com",
            "password": "userpassA123",
            "display_name": "User A",
        })
        token_a = reg_a.json()["access_token"]

        # Register user B
        reg_b = client.post("/api/v1/auth/register", json={
            "email": "userb@example.com",
            "password": "userpassB123",
            "display_name": "User B",
        })
        token_b = reg_b.json()["access_token"]

        # User A creates an item
        client.post(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"title": "A's Task"},
        )

        # User B creates an item
        client.post(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"title": "B's Task"},
        )

        # User A should see only their task (not B's)
        response = client.get(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        items = response.json()
        titles = [i["title"] for i in items]
        assert "A's Task" in titles
        assert "B's Task" not in titles
