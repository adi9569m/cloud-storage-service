"""Integration tests for public link sharing and unauthenticated link access."""

from datetime import datetime, timedelta, timezone
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
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.folder import Folder
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
    """Create a fresh isolated database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
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
    """Create a primary active test user."""
    user = User(
        email="creator@example.com",
        hashed_password=hash_password("CreatorPassword123!"),
        full_name="Creator User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_file(client, test_user):
    """Create a sample file via direct upload to ensure storage object exists."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    file_bytes = b"Hello Public World File Content"
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("shared_readme.txt", io.BytesIO(file_bytes), "text/plain")},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def sample_folder(client, test_user):
    """Create a sample folder with child items."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    folder_res = client.post(
        "/api/v1/folders",
        json={"name": "Public Assets"},
        headers=headers,
    )
    assert folder_res.status_code == 201
    folder = folder_res.json()

    # Upload file inside folder
    client.post(
        "/api/v1/files/upload",
        files={"file": ("asset.png", io.BytesIO(b"PNG binary image data"), "image/png")},
        data={"folder_id": folder["id"]},
        headers=headers,
    )

    return folder


def test_create_public_link_unprotected(client, test_user, sample_file):
    """Test generating a public link without password."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "file_id": sample_file["id"],
        "role": "VIEWER",
    }
    response = client.post("/api/v1/links", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["file_id"] == sample_file["id"]
    assert data["has_password"] is False
    assert data["is_active"] is True
    assert data["access_count"] == 0
    assert len(data["token"]) > 20


def test_create_public_link_with_password_and_expiry(client, test_user, sample_folder):
    """Test generating a protected public link with password and expiry date."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    future_time = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "folder_id": sample_folder["id"],
        "role": "VIEWER",
        "password": "SecretPassword123",
        "expires_at": future_time,
    }
    response = client.post("/api/v1/links", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["folder_id"] == sample_folder["id"]
    assert data["has_password"] is True
    assert data["expires_at"] is not None


def test_list_and_update_public_links(client, test_user, sample_file):
    """Test listing and updating public link configuration."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Create link
    create_res = client.post(
        "/api/v1/links",
        json={"file_id": sample_file["id"], "role": "VIEWER"},
        headers=headers,
    )
    link_id = create_res.json()["id"]

    # List links
    list_res = client.get(f"/api/v1/links/file/{sample_file['id']}", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Update: add password and toggle active
    update_res = client.put(
        f"/api/v1/links/{link_id}",
        json={"password": "NewPassword999", "is_active": False},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["has_password"] is True
    assert update_res.json()["is_active"] is False


def test_delete_public_link(client, test_user, sample_file):
    """Test revoking a public share link."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(
        "/api/v1/links",
        json={"file_id": sample_file["id"], "role": "VIEWER"},
        headers=headers,
    )
    link_id = create_res.json()["id"]
    share_token = create_res.json()["token"]

    # Delete link
    del_res = client.delete(f"/api/v1/links/{link_id}", headers=headers)
    assert del_res.status_code == 200

    # Public access now fails with 404
    public_res = client.get(f"/api/v1/public/links/{share_token}")
    assert public_res.status_code == 404


def test_public_link_unprotected_access_flow(client, test_user, sample_file):
    """Test public anonymous inspection and file download for an unprotected link."""
    auth_token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {auth_token}"}

    create_res = client.post(
        "/api/v1/links",
        json={"file_id": sample_file["id"], "role": "VIEWER"},
        headers=headers,
    )
    share_token = create_res.json()["token"]

    # 1. Unauthenticated inspection
    inspect_res = client.get(f"/api/v1/public/links/{share_token}")
    assert inspect_res.status_code == 200
    data = inspect_res.json()
    assert data["resource_type"] == "file"
    assert data["has_password"] is False
    assert data["requires_password"] is False
    assert data["file"]["name"] == "shared_readme.txt"
    assert data["download_url"] is not None

    # 2. Unauthenticated download
    dl_res = client.get(f"/api/v1/public/links/{share_token}/download")
    assert dl_res.status_code == 200
    assert dl_res.content == b"Hello Public World File Content"


def test_public_link_password_protection_flow(client, test_user, sample_file):
    """Test protected public link requires password validation."""
    auth_token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {auth_token}"}

    create_res = client.post(
        "/api/v1/links",
        json={"file_id": sample_file["id"], "password": "Protected1234!"},
        headers=headers,
    )
    share_token = create_res.json()["token"]

    # 1. Inspect without password -> requires_password = True
    inspect_res = client.get(f"/api/v1/public/links/{share_token}")
    assert inspect_res.status_code == 200
    assert inspect_res.json()["requires_password"] is True
    assert inspect_res.json()["file"] is None

    # 2. Access with wrong password -> 401 Unauthorized
    wrong_res = client.post(
        f"/api/v1/public/links/{share_token}/access",
        json={"password": "WrongPassword!"},
    )
    assert wrong_res.status_code == 401

    # 3. Access with valid password -> returns file
    valid_res = client.post(
        f"/api/v1/public/links/{share_token}/access",
        json={"password": "Protected1234!"},
    )
    assert valid_res.status_code == 200
    assert valid_res.json()["requires_password"] is False
    assert valid_res.json()["file"]["name"] == "shared_readme.txt"

    # 4. Download with password query parameter
    dl_res = client.get(f"/api/v1/public/links/{share_token}/download?password=Protected1234!")
    assert dl_res.status_code == 200
    assert dl_res.content == b"Hello Public World File Content"

    # 5. Download without password -> 401
    dl_fail_res = client.get(f"/api/v1/public/links/{share_token}/download")
    assert dl_fail_res.status_code == 401


def test_public_folder_contents_navigation(client, test_user, sample_folder):
    """Test browsing public folder contents."""
    auth_token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {auth_token}"}

    create_res = client.post(
        "/api/v1/links",
        json={"folder_id": sample_folder["id"], "role": "VIEWER"},
        headers=headers,
    )
    share_token = create_res.json()["token"]

    # Browse folder
    contents_res = client.get(f"/api/v1/public/links/{share_token}/contents")
    assert contents_res.status_code == 200
    data = contents_res.json()
    assert data["folder"]["name"] == "Public Assets"
    assert data["total_files"] == 1
    assert data["files"][0]["name"] == "asset.png"


def test_deactivated_and_expired_public_link(client, test_user, sample_file):
    """Test disabled or expired public links return 410 Gone."""
    auth_token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {auth_token}"}

    past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    # Create expired link
    create_res = client.post(
        "/api/v1/links",
        json={"file_id": sample_file["id"], "expires_at": past_time},
        headers=headers,
    )
    share_token = create_res.json()["token"]

    # Attempt to access expired link -> 410 Gone
    expired_res = client.get(f"/api/v1/public/links/{share_token}")
    assert expired_res.status_code == 410
    assert "expired" in expired_res.json()["detail"].lower()
