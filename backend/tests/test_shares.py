"""Integration tests for user-to-user sharing and role-based access control (RBAC)."""

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
from app.models.share import ShareRole
from app.models.user import User
from app.services.share_service import ShareService

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
def owner_user(db_session):
    """Create resource owner user."""
    user = User(
        email="owner@example.com",
        hashed_password=hash_password("OwnerPassword123!"),
        full_name="Owner User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def grantee_user(db_session):
    """Create recipient user to share with."""
    user = User(
        email="recipient@example.com",
        hashed_password=hash_password("RecipientPassword123!"),
        full_name="Recipient User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def other_user(db_session):
    """Create third unrelated user."""
    user = User(
        email="other@example.com",
        hashed_password=hash_password("OtherPassword123!"),
        full_name="Other User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_file(db_session, owner_user):
    """Create a sample file owned by owner_user."""
    file = File(
        name="project_proposal.pdf",
        owner_id=owner_user.id,
        mime_type="application/pdf",
        size_bytes=2048,
        storage_path=f"uploads/{owner_user.id}/files/{uuid.uuid4()}_project_proposal.pdf",
    )
    db_session.add(file)
    db_session.commit()
    db_session.refresh(file)

    ver = FileVersion(
        file_id=file.id,
        version_number=1,
        storage_path=file.storage_path,
        size_bytes=2048,
        mime_type="application/pdf",
        uploaded_by_id=owner_user.id,
    )
    db_session.add(ver)
    db_session.commit()
    return file


@pytest.fixture(scope="function")
def sample_folder(db_session, owner_user):
    """Create a sample folder owned by owner_user."""
    folder = Folder(
        name="Confidential Reports",
        owner_id=owner_user.id,
    )
    db_session.add(folder)
    db_session.commit()
    db_session.refresh(folder)
    return folder


def test_create_file_share_success(client, owner_user, grantee_user, sample_file):
    """Test sharing a file with another user by email with default VIEWER role."""
    token = create_access_token(subject=str(owner_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "grantee_email": grantee_user.email,
        "file_id": str(sample_file.id),
        "role": "VIEWER",
    }
    response = client.post("/api/v1/shares", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["granter_id"] == str(owner_user.id)
    assert data["grantee_id"] == str(grantee_user.id)
    assert data["file_id"] == str(sample_file.id)
    assert data["folder_id"] is None
    assert data["role"] == "VIEWER"
    assert data["grantee_email"] == grantee_user.email


def test_create_folder_share_success(client, owner_user, grantee_user, sample_folder):
    """Test sharing a folder with EDITOR role."""
    token = create_access_token(subject=str(owner_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "grantee_email": grantee_user.email,
        "folder_id": str(sample_folder.id),
        "role": "EDITOR",
    }
    response = client.post("/api/v1/shares", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["granter_id"] == str(owner_user.id)
    assert data["grantee_id"] == str(grantee_user.id)
    assert data["folder_id"] == str(sample_folder.id)
    assert data["role"] == "EDITOR"


def test_create_share_nonexistent_grantee(client, owner_user, sample_file):
    """Test sharing with a non-existent email returns 404."""
    token = create_access_token(subject=str(owner_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "grantee_email": "nonexistent@example.com",
        "file_id": str(sample_file.id),
        "role": "VIEWER",
    }
    response = client.post("/api/v1/shares", json=payload, headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_share_with_self_rejected(client, owner_user, sample_file):
    """Test sharing with oneself returns 400 Bad Request."""
    token = create_access_token(subject=str(owner_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "grantee_email": owner_user.email,
        "file_id": str(sample_file.id),
        "role": "VIEWER",
    }
    response = client.post("/api/v1/shares", json=payload, headers=headers)
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"].lower()


def test_create_share_non_owner_forbidden(client, other_user, grantee_user, sample_file):
    """Test non-owner user cannot share another user's file."""
    token = create_access_token(subject=str(other_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "grantee_email": grantee_user.email,
        "file_id": str(sample_file.id),
        "role": "VIEWER",
    }
    response = client.post("/api/v1/shares", json=payload, headers=headers)
    assert response.status_code == 403


def test_create_share_duplicate_updates_role(client, owner_user, grantee_user, sample_file):
    """Test sharing with the same user again updates their role instead of erroring."""
    token = create_access_token(subject=str(owner_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Initial share with VIEWER
    payload1 = {
        "grantee_email": grantee_user.email,
        "file_id": str(sample_file.id),
        "role": "VIEWER",
    }
    res1 = client.post("/api/v1/shares", json=payload1, headers=headers)
    assert res1.status_code == 201
    share_id = res1.json()["id"]

    # Re-share with EDITOR
    payload2 = {
        "grantee_email": grantee_user.email,
        "file_id": str(sample_file.id),
        "role": "EDITOR",
    }
    res2 = client.post("/api/v1/shares", json=payload2, headers=headers)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["id"] == share_id
    assert data2["role"] == "EDITOR"


def test_update_share_role(client, owner_user, grantee_user, other_user, sample_file):
    """Test updating a share's role directly via PUT /shares/{id}."""
    owner_token = create_access_token(subject=str(owner_user.id))
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create_res = client.post(
        "/api/v1/shares",
        json={"grantee_email": grantee_user.email, "file_id": str(sample_file.id), "role": "VIEWER"},
        headers=owner_headers,
    )
    share_id = create_res.json()["id"]

    # Owner updates role to EDITOR
    update_res = client.put(
        f"/api/v1/shares/{share_id}",
        json={"role": "EDITOR"},
        headers=owner_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["role"] == "EDITOR"

    # Other user attempts update -> 403 Forbidden
    other_token = create_access_token(subject=str(other_user.id))
    other_headers = {"Authorization": f"Bearer {other_token}"}
    unauth_res = client.put(
        f"/api/v1/shares/{share_id}",
        json={"role": "VIEWER"},
        headers=other_headers,
    )
    assert unauth_res.status_code == 403


def test_revoke_share(client, owner_user, grantee_user, sample_file):
    """Test revoking a share record."""
    owner_token = create_access_token(subject=str(owner_user.id))
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create_res = client.post(
        "/api/v1/shares",
        json={"grantee_email": grantee_user.email, "file_id": str(sample_file.id), "role": "VIEWER"},
        headers=owner_headers,
    )
    share_id = create_res.json()["id"]

    # Delete share
    delete_res = client.delete(f"/api/v1/shares/{share_id}", headers=owner_headers)
    assert delete_res.status_code == 200
    assert "revoked" in delete_res.json()["message"].lower()

    # Re-fetch -> 404
    get_res = client.put(
        f"/api/v1/shares/{share_id}",
        json={"role": "EDITOR"},
        headers=owner_headers,
    )
    assert get_res.status_code == 404


def test_list_shares_on_resource(client, owner_user, grantee_user, sample_file, sample_folder):
    """Test listing shares on a file and folder."""
    token = create_access_token(subject=str(owner_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Share file and folder
    client.post(
        "/api/v1/shares",
        json={"grantee_email": grantee_user.email, "file_id": str(sample_file.id), "role": "VIEWER"},
        headers=headers,
    )
    client.post(
        "/api/v1/shares",
        json={"grantee_email": grantee_user.email, "folder_id": str(sample_folder.id), "role": "EDITOR"},
        headers=headers,
    )

    # List file shares
    file_shares_res = client.get(f"/api/v1/shares/file/{sample_file.id}", headers=headers)
    assert file_shares_res.status_code == 200
    assert len(file_shares_res.json()) == 1
    assert file_shares_res.json()[0]["grantee_email"] == grantee_user.email

    # List folder shares
    folder_shares_res = client.get(f"/api/v1/shares/folder/{sample_folder.id}", headers=headers)
    assert folder_shares_res.status_code == 200
    assert len(folder_shares_res.json()) == 1
    assert folder_shares_res.json()[0]["role"] == "EDITOR"


def test_shared_with_me_and_shared_by_me(client, owner_user, grantee_user, sample_file, sample_folder):
    """Test 'Shared with Me' and 'Shared by Me' listings."""
    owner_token = create_access_token(subject=str(owner_user.id))
    grantee_token = create_access_token(subject=str(grantee_user.id))

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    grantee_headers = {"Authorization": f"Bearer {grantee_token}"}

    # Create shares
    client.post(
        "/api/v1/shares",
        json={"grantee_email": grantee_user.email, "file_id": str(sample_file.id), "role": "VIEWER"},
        headers=owner_headers,
    )
    client.post(
        "/api/v1/shares",
        json={"grantee_email": grantee_user.email, "folder_id": str(sample_folder.id), "role": "EDITOR"},
        headers=owner_headers,
    )

    # Check Shared by Me (Owner)
    by_me_res = client.get("/api/v1/shares/shared-by-me", headers=owner_headers)
    assert by_me_res.status_code == 200
    by_me_data = by_me_res.json()
    assert by_me_data["total_count"] == 2

    # Check Shared with Me (Grantee)
    with_me_res = client.get("/api/v1/shares/shared-with-me", headers=grantee_headers)
    assert with_me_res.status_code == 200
    with_me_data = with_me_res.json()
    assert with_me_data["total_count"] == 2
    assert len(with_me_data["files"]) == 1
    assert len(with_me_data["folders"]) == 1
    assert with_me_data["files"][0]["file"]["name"] == "project_proposal.pdf"
    assert with_me_data["folders"][0]["folder"]["name"] == "Confidential Reports"


def test_inherited_folder_share_access_check(db_session, owner_user, grantee_user, other_user):
    """Test ShareService.check_user_access resolves permissions on nested files and folders."""
    # Create parent folder
    parent_folder = Folder(name="Root Share Folder", owner_id=owner_user.id)
    db_session.add(parent_folder)
    db_session.commit()
    db_session.refresh(parent_folder)

    # Create child subfolder
    child_folder = Folder(name="Sub Folder", owner_id=owner_user.id, parent_id=parent_folder.id)
    db_session.add(child_folder)
    db_session.commit()
    db_session.refresh(child_folder)

    # Create file inside subfolder
    nested_file = File(
        name="nested_doc.txt",
        owner_id=owner_user.id,
        folder_id=child_folder.id,
        mime_type="text/plain",
        size_bytes=100,
        storage_path="uploads/nested_doc.txt",
    )
    db_session.add(nested_file)
    db_session.commit()
    db_session.refresh(nested_file)

    # Owner has access
    has_acc, role = ShareService.check_user_access(db_session, user_id=owner_user.id, file_id=nested_file.id)
    assert has_acc is True
    assert role == "OWNER"

    # Grantee before share -> No access
    has_acc, _ = ShareService.check_user_access(db_session, user_id=grantee_user.id, file_id=nested_file.id)
    assert has_acc is False

    # Share parent folder with grantee as EDITOR
    from app.models.share import Share
    share = Share(
        granter_id=owner_user.id,
        grantee_id=grantee_user.id,
        folder_id=parent_folder.id,
        role=ShareRole.EDITOR,
    )
    db_session.add(share)
    db_session.commit()

    # Now grantee has inherited access on child folder and nested file
    has_acc, role = ShareService.check_user_access(db_session, user_id=grantee_user.id, folder_id=child_folder.id)
    assert has_acc is True
    assert role == "EDITOR"

    has_acc, role = ShareService.check_user_access(db_session, user_id=grantee_user.id, file_id=nested_file.id)
    assert has_acc is True
    assert role == "EDITOR"

    # Other user still has no access
    has_acc, _ = ShareService.check_user_access(db_session, user_id=other_user.id, file_id=nested_file.id)
    assert has_acc is False
