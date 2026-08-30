"""Integration tests for Starred/Favorites management and unified listing."""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create an isolated test database session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create active user."""
    user = User(
        email="starrertest@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Star User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def other_user(db_session):
    """Create second user for isolation checks."""
    user = User(
        email="otherstar@example.com",
        hashed_password=hash_password("OtherPassword123!"),
        full_name="Other Star User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_toggle_star_file_and_unified_list(client, test_user):
    """Test starring and unstarring files, and querying the unified /stars endpoint."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Upload file
    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("favorite_notes.md", io.BytesIO(b"# Notes"), "text/markdown")},
        headers=headers,
    )
    file_id = upload_res.json()["id"]

    # Initial list -> 0 starred
    initial_res = client.get("/api/v1/stars", headers=headers)
    assert initial_res.status_code == 200
    assert initial_res.json()["total_count"] == 0

    # Star the file
    star_res = client.post("/api/v1/stars/toggle", json={"file_id": file_id}, headers=headers)
    assert star_res.status_code == 200
    assert star_res.json()["is_starred"] is True
    assert star_res.json()["resource_type"] == "file"

    # Query /stars -> 1 file
    list_res = client.get("/api/v1/stars", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total_count"] == 1
    assert len(data["files"]) == 1
    assert data["files"][0]["id"] == file_id
    assert data["files"][0]["is_starred"] is True

    # Unstar the file
    unstar_res = client.post("/api/v1/stars/toggle", json={"file_id": file_id}, headers=headers)
    assert unstar_res.status_code == 200
    assert unstar_res.json()["is_starred"] is False

    # Query /stars -> 0
    empty_res = client.get("/api/v1/stars", headers=headers)
    assert empty_res.json()["total_count"] == 0


def test_toggle_star_folder_and_unified_list(client, test_user):
    """Test starring folder and retrieving combined list of starred folders and files."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Create folder & file
    folder_res = client.post("/api/v1/folders", json={"name": "Starred Projects"}, headers=headers)
    folder_id = folder_res.json()["id"]

    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("spec.pdf", io.BytesIO(b"spec data"), "application/pdf")},
        headers=headers,
    )
    file_id = upload_res.json()["id"]

    # Star both
    client.post("/api/v1/stars/toggle", json={"folder_id": folder_id}, headers=headers)
    client.post("/api/v1/stars/toggle", json={"file_id": file_id}, headers=headers)

    # Query unified /stars
    list_res = client.get("/api/v1/stars", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total_count"] == 2
    assert len(data["folders"]) == 1
    assert len(data["files"]) == 1
    assert data["folders"][0]["name"] == "Starred Projects"
    assert data["files"][0]["name"] == "spec.pdf"


def test_star_unauthorized_isolation(client, test_user, other_user):
    """Test user cannot star another user's private file."""
    user_token = create_access_token(subject=str(test_user.id))
    other_token = create_access_token(subject=str(other_user.id))

    # User 1 creates file
    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("private.txt", io.BytesIO(b"Private data"), "text/plain")},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    file_id = upload_res.json()["id"]

    # User 2 attempts to star User 1's file -> 403
    star_res = client.post(
        "/api/v1/stars/toggle",
        json={"file_id": file_id},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert star_res.status_code == 403
