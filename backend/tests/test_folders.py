"""Comprehensive integration tests for Folder management, hierarchy, moves, cascades, and favorites."""

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
from app.models.folder import Folder
from app.models.user import User

# Setup in-memory SQLite database for testing
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
        email="user1@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="User One",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def other_user(db_session):
    """Create a secondary active test user for multi-tenancy access checks."""
    user = User(
        email="user2@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="User Two",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Generate authorization headers for the primary test user."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def other_auth_headers(other_user):
    """Generate authorization headers for the secondary test user."""
    token = create_access_token(subject=str(other_user.id))
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. Folder Creation Tests
# ============================================================================

def test_create_root_folder_success(client, auth_headers):
    """Test creating a top-level root directory."""
    payload = {"name": "Documents", "color": "#3B82F6"}
    response = client.post("/api/v1/folders", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Documents"
    assert data["parent_id"] is None
    assert data["color"] == "#3B82F6"
    assert data["is_deleted"] is False
    assert data["is_starred"] is False
    assert "id" in data


def test_create_nested_folder_success(client, auth_headers):
    """Test creating a subfolder inside a parent directory."""
    # Create parent
    parent_resp = client.post("/api/v1/folders", json={"name": "Projects"}, headers=auth_headers)
    assert parent_resp.status_code == 201
    parent_id = parent_resp.json()["id"]

    # Create child
    child_payload = {"name": "Backend", "parent_id": parent_id, "color": "#10B981"}
    child_resp = client.post("/api/v1/folders", json=child_payload, headers=auth_headers)
    assert child_resp.status_code == 201
    child_data = child_resp.json()
    assert child_data["name"] == "Backend"
    assert child_data["parent_id"] == parent_id
    assert child_data["color"] == "#10B981"


def test_create_folder_duplicate_name_conflict(client, auth_headers):
    """Test that creating a sibling folder with the same name returns 409 Conflict."""
    client.post("/api/v1/folders", json={"name": "Photos"}, headers=auth_headers)

    # Attempt duplicate at root (case-insensitive check)
    dup_resp = client.post("/api/v1/folders", json={"name": "photos"}, headers=auth_headers)
    assert dup_resp.status_code == 409
    assert "already exists" in dup_resp.json()["detail"]


def test_create_folder_same_name_in_different_parents_allowed(client, auth_headers):
    """Test that folders with the same name under different parents are allowed."""
    p1 = client.post("/api/v1/folders", json={"name": "Parent1"}, headers=auth_headers).json()["id"]
    p2 = client.post("/api/v1/folders", json={"name": "Parent2"}, headers=auth_headers).json()["id"]

    r1 = client.post("/api/v1/folders", json={"name": "Sub", "parent_id": p1}, headers=auth_headers)
    r2 = client.post("/api/v1/folders", json={"name": "Sub", "parent_id": p2}, headers=auth_headers)
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_create_folder_invalid_name(client, auth_headers):
    """Test creating a folder with invalid or empty names returns 422."""
    # Empty string
    r1 = client.post("/api/v1/folders", json={"name": ""}, headers=auth_headers)
    assert r1.status_code == 422

    # Whitespace only
    r2 = client.post("/api/v1/folders", json={"name": "   "}, headers=auth_headers)
    assert r2.status_code == 422

    # Path separator
    r3 = client.post("/api/v1/folders", json={"name": "Invalid/Name"}, headers=auth_headers)
    assert r3.status_code == 422


def test_create_folder_nonexistent_parent(client, auth_headers):
    """Test creating a folder with an invalid parent UUID returns 404."""
    fake_parent_id = str(uuid.uuid4())
    resp = client.post("/api/v1/folders", json={"name": "Orphan", "parent_id": fake_parent_id}, headers=auth_headers)
    assert resp.status_code == 404


# ============================================================================
# 2. Navigation, Details, and Breadcrumbs Tests
# ============================================================================

def test_get_root_contents(client, auth_headers, test_user, db_session):
    """Test listing root directory items and breadcrumbs."""
    # Create two root folders
    client.post("/api/v1/folders", json={"name": "Beta"}, headers=auth_headers)
    client.post("/api/v1/folders", json={"name": "Alpha"}, headers=auth_headers)

    # Create root file directly in db
    root_file = File(
        name="root_notes.txt",
        folder_id=None,
        owner_id=test_user.id,
        mime_type="text/plain",
        size_bytes=1024,
        storage_path="uploads/root_notes.txt",
    )
    db_session.add(root_file)
    db_session.commit()

    resp = client.get("/api/v1/folders", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_folder"] is None
    assert len(data["breadcrumbs"]) == 1
    assert data["breadcrumbs"][0]["name"] == "My Drive"
    assert data["total_folders"] == 2
    assert data["total_files"] == 1
    # Sorted by name ascending by default
    assert data["folders"][0]["name"] == "Alpha"
    assert data["folders"][1]["name"] == "Beta"


def test_get_folder_details_with_breadcrumbs(client, auth_headers, test_user, db_session):
    """Test hierarchical breadcrumbs generation across multiple levels."""
    # Level 1: Root -> Documents
    f1 = client.post("/api/v1/folders", json={"name": "Documents"}, headers=auth_headers).json()["id"]
    # Level 2: Documents -> Invoices
    f2 = client.post("/api/v1/folders", json={"name": "Invoices", "parent_id": f1}, headers=auth_headers).json()["id"]
    # Level 3: Invoices -> 2026
    f3 = client.post("/api/v1/folders", json={"name": "2026", "parent_id": f2}, headers=auth_headers).json()["id"]

    # Add child file in 2026
    child_file = File(
        name="january.pdf",
        folder_id=uuid.UUID(f3),
        owner_id=test_user.id,
        mime_type="application/pdf",
        size_bytes=2048,
        storage_path="uploads/january.pdf",
    )
    db_session.add(child_file)
    db_session.commit()

    # Query folder details
    resp = client.get(f"/api/v1/folders/{f3}", headers=auth_headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["name"] == "2026"
    assert detail["files_count"] == 1
    assert detail["subfolders_count"] == 0

    # Verify breadcrumb trail: My Drive -> Documents -> Invoices -> 2026
    crumbs = detail["breadcrumbs"]
    assert len(crumbs) == 4
    assert crumbs[0]["name"] == "My Drive"
    assert crumbs[0]["id"] is None
    assert crumbs[1]["name"] == "Documents"
    assert crumbs[1]["id"] == f1
    assert crumbs[2]["name"] == "Invoices"
    assert crumbs[2]["id"] == f2
    assert crumbs[3]["name"] == "2026"
    assert crumbs[3]["id"] == f3


def test_get_folder_contents_endpoint(client, auth_headers, test_user, db_session):
    """Test GET /api/v1/folders/{id}/contents."""
    parent = client.post("/api/v1/folders", json={"name": "Parent"}, headers=auth_headers).json()["id"]
    client.post("/api/v1/folders", json={"name": "ChildFolder", "parent_id": parent}, headers=auth_headers)

    child_file = File(
        name="doc.txt",
        folder_id=uuid.UUID(parent),
        owner_id=test_user.id,
        mime_type="text/plain",
        size_bytes=512,
        storage_path="uploads/doc.txt",
    )
    db_session.add(child_file)
    db_session.commit()

    resp = client.get(f"/api/v1/folders/{parent}/contents", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_folder"]["id"] == parent
    assert len(data["folders"]) == 1
    assert len(data["files"]) == 1
    assert data["total_folders"] == 1
    assert data["total_files"] == 1


def test_get_folder_tree(client, auth_headers):
    """Test full directory tree hierarchy generation."""
    # Root A
    root_a = client.post("/api/v1/folders", json={"name": "A"}, headers=auth_headers).json()["id"]
    # Root B
    root_b = client.post("/api/v1/folders", json={"name": "B"}, headers=auth_headers).json()["id"]
    # A -> A1
    a1 = client.post("/api/v1/folders", json={"name": "A1", "parent_id": root_a}, headers=auth_headers).json()["id"]
    # A1 -> A1_Sub
    client.post("/api/v1/folders", json={"name": "A1_Sub", "parent_id": a1}, headers=auth_headers)

    resp = client.get("/api/v1/folders/tree", headers=auth_headers)
    assert resp.status_code == 200
    tree = resp.json()
    assert len(tree) == 2
    assert tree[0]["name"] == "A"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "A1"
    assert len(tree[0]["children"][0]["children"]) == 1
    assert tree[0]["children"][0]["children"][0]["name"] == "A1_Sub"
    assert tree[1]["name"] == "B"
    assert len(tree[1]["children"]) == 0


# ============================================================================
# 3. Update & Rename Tests
# ============================================================================

def test_update_folder_rename_and_color(client, auth_headers):
    """Test updating folder display name and color tag."""
    folder_id = client.post("/api/v1/folders", json={"name": "OldName"}, headers=auth_headers).json()["id"]

    update_payload = {"name": "NewName", "color": "#EF4444"}
    resp = client.put(f"/api/v1/folders/{folder_id}", json=update_payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "NewName"
    assert data["color"] == "#EF4444"


def test_update_folder_duplicate_name_conflict(client, auth_headers):
    """Test renaming a folder to an existing sibling's name returns 409."""
    client.post("/api/v1/folders", json={"name": "Sibling1"}, headers=auth_headers)
    f2 = client.post("/api/v1/folders", json={"name": "Sibling2"}, headers=auth_headers).json()["id"]

    resp = client.put(f"/api/v1/folders/{f2}", json={"name": "Sibling1"}, headers=auth_headers)
    assert resp.status_code == 409


# ============================================================================
# 4. Move & Cycle Prevention Tests
# ============================================================================

def test_move_folder_to_another_parent(client, auth_headers):
    """Test successfully moving a folder to another parent directory."""
    dir1 = client.post("/api/v1/folders", json={"name": "Dir1"}, headers=auth_headers).json()["id"]
    dir2 = client.post("/api/v1/folders", json={"name": "Dir2"}, headers=auth_headers).json()["id"]
    sub = client.post("/api/v1/folders", json={"name": "Sub", "parent_id": dir1}, headers=auth_headers).json()["id"]

    # Move Sub from Dir1 to Dir2
    resp = client.post(f"/api/v1/folders/{sub}/move", json={"destination_parent_id": dir2}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["parent_id"] == dir2


def test_move_folder_to_root(client, auth_headers):
    """Test moving a nested folder back to the root level."""
    parent = client.post("/api/v1/folders", json={"name": "Parent"}, headers=auth_headers).json()["id"]
    sub = client.post("/api/v1/folders", json={"name": "Sub", "parent_id": parent}, headers=auth_headers).json()["id"]

    resp = client.post(f"/api/v1/folders/{sub}/move", json={"destination_parent_id": None}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["parent_id"] is None


def test_move_folder_into_self_rejected(client, auth_headers):
    """Test that attempting to move a folder into itself returns 400 Bad Request."""
    folder_id = client.post("/api/v1/folders", json={"name": "FolderX"}, headers=auth_headers).json()["id"]

    resp = client.post(f"/api/v1/folders/{folder_id}/move", json={"destination_parent_id": folder_id}, headers=auth_headers)
    assert resp.status_code == 400
    assert "Cannot move a folder into itself" in resp.json()["detail"]


def test_move_folder_into_descendant_rejected(client, auth_headers):
    """Test circular hierarchy prevention (moving a parent into its grandchild)."""
    # A -> B -> C
    a = client.post("/api/v1/folders", json={"name": "NodeA"}, headers=auth_headers).json()["id"]
    b = client.post("/api/v1/folders", json={"name": "NodeB", "parent_id": a}, headers=auth_headers).json()["id"]
    c = client.post("/api/v1/folders", json={"name": "NodeC", "parent_id": b}, headers=auth_headers).json()["id"]

    # Attempt to move A into C
    resp = client.post(f"/api/v1/folders/{a}/move", json={"destination_parent_id": c}, headers=auth_headers)
    assert resp.status_code == 400
    assert "subdirectories" in resp.json()["detail"]


def test_move_folder_name_conflict_in_destination(client, auth_headers):
    """Test moving a folder where the destination already has a folder of the same name."""
    dest = client.post("/api/v1/folders", json={"name": "Destination"}, headers=auth_headers).json()["id"]
    client.post("/api/v1/folders", json={"name": "SharedName", "parent_id": dest}, headers=auth_headers)
    src = client.post("/api/v1/folders", json={"name": "SharedName"}, headers=auth_headers).json()["id"]

    resp = client.post(f"/api/v1/folders/{src}/move", json={"destination_parent_id": dest}, headers=auth_headers)
    assert resp.status_code == 409


# ============================================================================
# 5. Soft Delete, Restore & Hard Delete Tests
# ============================================================================

def test_soft_delete_and_cascade_descendants(client, auth_headers, test_user, db_session):
    """Test soft deleting a folder cascades is_deleted flag to all child folders and files."""
    parent = client.post("/api/v1/folders", json={"name": "ParentDel"}, headers=auth_headers).json()["id"]
    child = client.post("/api/v1/folders", json={"name": "ChildDel", "parent_id": parent}, headers=auth_headers).json()["id"]

    child_file = File(
        name="child.txt",
        folder_id=uuid.UUID(child),
        owner_id=test_user.id,
        mime_type="text/plain",
        size_bytes=100,
        storage_path="uploads/child.txt",
    )
    db_session.add(child_file)
    db_session.commit()

    # Soft delete parent
    del_resp = client.delete(f"/api/v1/folders/{parent}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_deleted"] is True

    # Check child folder in db
    c_folder = db_session.query(Folder).filter(Folder.id == uuid.UUID(child)).first()
    assert c_folder.is_deleted is True
    assert c_folder.deleted_at is not None

    # Check child file in db
    c_file = db_session.query(File).filter(File.folder_id == uuid.UUID(child)).first()
    assert c_file.is_deleted is True
    assert c_file.deleted_at is not None


def test_restore_folder_and_descendants(client, auth_headers, db_session):
    """Test restoring a folder restores all soft-deleted children."""
    parent = client.post("/api/v1/folders", json={"name": "ParentRes"}, headers=auth_headers).json()["id"]
    child = client.post("/api/v1/folders", json={"name": "ChildRes", "parent_id": parent}, headers=auth_headers).json()["id"]

    # Soft delete
    client.delete(f"/api/v1/folders/{parent}", headers=auth_headers)

    # Restore
    res_resp = client.post(f"/api/v1/folders/{parent}/restore", headers=auth_headers)
    assert res_resp.status_code == 200
    assert res_resp.json()["is_deleted"] is False

    # Check child folder in db
    c_folder = db_session.query(Folder).filter(Folder.id == uuid.UUID(child)).first()
    assert c_folder.is_deleted is False
    assert c_folder.deleted_at is None


def test_restore_folder_with_deleted_parent_moves_to_root(client, auth_headers, db_session):
    """Test restoring a child whose parent remains deleted resets child's parent_id to root."""
    parent = client.post("/api/v1/folders", json={"name": "P"}, headers=auth_headers).json()["id"]
    child = client.post("/api/v1/folders", json={"name": "C", "parent_id": parent}, headers=auth_headers).json()["id"]

    # Delete both
    client.delete(f"/api/v1/folders/{parent}", headers=auth_headers)

    # Restore only child
    res_resp = client.post(f"/api/v1/folders/{child}/restore", headers=auth_headers)
    assert res_resp.status_code == 200
    assert res_resp.json()["parent_id"] is None


def test_permanent_delete_folder(client, auth_headers, db_session):
    """Test permanent deletion purges the folder from database."""
    folder_id = client.post("/api/v1/folders", json={"name": "Temp"}, headers=auth_headers).json()["id"]

    resp = client.delete(f"/api/v1/folders/{folder_id}/permanent", headers=auth_headers)
    assert resp.status_code == 204

    # Verify folder is completely gone from db
    f = db_session.query(Folder).filter(Folder.id == uuid.UUID(folder_id)).first()
    assert f is None


# ============================================================================
# 6. Star / Favorite Tests
# ============================================================================

def test_toggle_star_folder(client, auth_headers):
    """Test starring and unstarring a folder."""
    folder_id = client.post("/api/v1/folders", json={"name": "FavoriteDocs"}, headers=auth_headers).json()["id"]

    # Star folder
    s1 = client.post(f"/api/v1/folders/{folder_id}/star", headers=auth_headers)
    assert s1.status_code == 200
    assert s1.json()["is_starred"] is True

    # Check detail returns is_starred = True
    d1 = client.get(f"/api/v1/folders/{folder_id}", headers=auth_headers).json()
    assert d1["is_starred"] is True

    # Unstar folder
    s2 = client.post(f"/api/v1/folders/{folder_id}/star", headers=auth_headers)
    assert s2.status_code == 200
    assert s2.json()["is_starred"] is False

    # Check detail returns is_starred = False
    d2 = client.get(f"/api/v1/folders/{folder_id}", headers=auth_headers).json()
    assert d2["is_starred"] is False


# ============================================================================
# 7. Multi-Tenant Access Control & Isolation Tests
# ============================================================================

def test_folder_access_control_isolation(client, auth_headers, other_auth_headers):
    """Test that User Two cannot view, edit, move, delete, or star User One's folder."""
    user1_folder = client.post("/api/v1/folders", json={"name": "PrivateUser1"}, headers=auth_headers).json()["id"]

    # User 2 attempts to get details
    r1 = client.get(f"/api/v1/folders/{user1_folder}", headers=other_auth_headers)
    assert r1.status_code == 404

    # User 2 attempts to update
    r2 = client.put(f"/api/v1/folders/{user1_folder}", json={"name": "Hacked"}, headers=other_auth_headers)
    assert r2.status_code == 404

    # User 2 attempts to delete
    r3 = client.delete(f"/api/v1/folders/{user1_folder}", headers=other_auth_headers)
    assert r3.status_code == 404

    # User 2 attempts to star
    r4 = client.post(f"/api/v1/folders/{user1_folder}/star", headers=other_auth_headers)
    assert r4.status_code == 404
