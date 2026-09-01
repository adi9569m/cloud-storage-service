"""Integration tests for Storage Analytics, Metrics, Category Breakdown, and Quota Enforcement."""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.file import File
from app.models.folder import Folder
from app.models.user import User
from app.services.storage_service import StorageService

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create an isolated database session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client."""
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
        email="storageuser@example.com",
        hashed_password=hash_password("StoragePass123!"),
        full_name="Storage Analytics User",
        is_active=True,
        storage_used_bytes=100000,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Generate bearer token headers."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def seed_storage_files(db_session, test_user):
    """Seed files of multiple categories and sizes."""
    files = [
        File(
            name="photo1.jpg",
            owner_id=test_user.id,
            mime_type="image/jpeg",
            size_bytes=40000,
            storage_path="uploads/photo1.jpg",
        ),
        File(
            name="document.pdf",
            owner_id=test_user.id,
            mime_type="application/pdf",
            size_bytes=30000,
            storage_path="uploads/document.pdf",
        ),
        File(
            name="music.mp3",
            owner_id=test_user.id,
            mime_type="audio/mpeg",
            size_bytes=20000,
            storage_path="uploads/music.mp3",
        ),
        File(
            name="code.py",
            owner_id=test_user.id,
            mime_type="text/x-python",
            size_bytes=10000,
            storage_path="uploads/code.py",
        ),
    ]
    db_session.add_all(files)

    # Add soft deleted file
    trash_file = File(
        name="deleted.zip",
        owner_id=test_user.id,
        mime_type="application/zip",
        size_bytes=15000,
        storage_path="uploads/deleted.zip",
        is_deleted=True,
    )
    db_session.add(trash_file)
    db_session.commit()
    return files


def test_get_storage_summary(client, auth_headers, seed_storage_files):
    """Test storage summary metrics and category breakdown calculation."""
    resp = client.get("/api/v1/storage/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["storage_used_bytes"] == 100000
    assert data["storage_quota_bytes"] == settings.DEFAULT_STORAGE_QUOTA_BYTES
    assert data["storage_available_bytes"] == settings.DEFAULT_STORAGE_QUOTA_BYTES - 100000
    assert data["total_files"] == 4
    assert data["trash_bytes"] == 15000

    # Verify category breakdown list
    breakdown_map = {item["category"]: item for item in data["breakdown"]}
    assert breakdown_map["images"]["bytes_used"] == 40000
    assert breakdown_map["images"]["file_count"] == 1
    assert breakdown_map["documents"]["bytes_used"] == 30000
    assert breakdown_map["audio"]["bytes_used"] == 20000
    assert breakdown_map["code"]["bytes_used"] == 10000

    # Verify largest files
    assert len(data["largest_files"]) == 4
    assert data["largest_files"][0]["name"] == "photo1.jpg"
    assert data["largest_files"][0]["size_bytes"] == 40000


def test_get_storage_breakdown_endpoint(client, auth_headers, seed_storage_files):
    """Test dedicated breakdown endpoint."""
    resp = client.get("/api/v1/storage/breakdown", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    categories = {item["category"] for item in data}
    assert "images" in categories
    assert "documents" in categories
    assert "code" in categories


def test_recalculate_storage(client, auth_headers, seed_storage_files, db_session, test_user):
    """Test recalculating user storage usage from database files table."""
    # Seed files sum = 40000 + 30000 + 20000 + 10000 = 100000
    resp = client.post("/api/v1/storage/recalculate", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["storage_used_bytes"] == 100000


def test_quota_exceeded_rejection_on_upload(client, auth_headers, db_session, test_user):
    """Test upload rejected with 413 when approaching/exceeding storage quota."""
    # Set user storage used near limit
    test_user.storage_used_bytes = settings.DEFAULT_STORAGE_QUOTA_BYTES - 10
    db_session.commit()

    # Try uploading a 100-byte file (which exceeds remaining 10 bytes)
    file_payload = {"file": ("test_overflow.txt", b"A" * 100, "text/plain")}
    resp = client.post("/api/v1/files/upload", headers=auth_headers, files=file_payload)
    assert resp.status_code == 413
    assert "Storage quota exceeded" in resp.json()["detail"]
