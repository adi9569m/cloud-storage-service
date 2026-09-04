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
from app.models.tag import ItemTag, Tag
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
        email="taguser@example.com",
        hashed_password=hash_password("TagPassword123!"),
        full_name="Tag User",
        is_active=True,
        storage_used_bytes=0,
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
def seed_items(db_session, test_user):
    """Seed test files and folders for tagging."""
    folder = Folder(name="WorkDocs", owner_id=test_user.id)
    db_session.add(folder)
    db_session.flush()

    file = File(
        name="invoice.pdf",
        owner_id=test_user.id,
        folder_id=folder.id,
        mime_type="application/pdf",
        size_bytes=4000,
        storage_path="uploads/invoice.pdf",
    )
    db_session.add(file)
    db_session.commit()
    return {"folder": folder, "file": file}

def test_create_and_list_tags(client, auth_headers):
    """Test creating custom color tags and querying user tag list."""

    resp1 = client.post("/api/v1/tags", headers=auth_headers, json={"name": "Finance", "color": "#10B981"})
    assert resp1.status_code == 201
    tag1 = resp1.json()
    assert tag1["name"] == "Finance"
    assert tag1["color"] == "#10B981"
    assert tag1["item_count"] == 0

    resp2 = client.post("/api/v1/tags", headers=auth_headers, json={"name": "Important", "color": "#EF4444"})
    assert resp2.status_code == 201

    dup = client.post("/api/v1/tags", headers=auth_headers, json={"name": "Finance", "color": "#000000"})
    assert dup.status_code == 409

    resp_list = client.get("/api/v1/tags", headers=auth_headers)
    assert resp_list.status_code == 200
    tags = resp_list.json()
    assert len(tags) == 2
    names = [t["name"] for t in tags]
    assert "Finance" in names
    assert "Important" in names

def test_update_and_delete_tag(client, auth_headers):
    """Test updating tag properties and deletion."""
    resp = client.post("/api/v1/tags", headers=auth_headers, json={"name": "Drafts", "color": "#9CA3AF"})
    tag_id = resp.json()["id"]

    resp_up = client.put(f"/api/v1/tags/{tag_id}", headers=auth_headers, json={"name": "Work Drafts", "color": "#6B7280"})
    assert resp_up.status_code == 200
    assert resp_up.json()["name"] == "Work Drafts"
    assert resp_up.json()["color"] == "#6B7280"

    resp_del = client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)
    assert resp_del.status_code == 204

    resp_list = client.get("/api/v1/tags", headers=auth_headers)
    assert len(resp_list.json()) == 0

def test_attach_and_detach_tag(client, auth_headers, seed_items):
    """Test attaching and detaching tags to files and folders and inspecting tagged collections."""
    tag_res = client.post("/api/v1/tags", headers=auth_headers, json={"name": "Invoices", "color": "#F59E0B"})
    tag_id = tag_res.json()["id"]

    file_id = str(seed_items["file"].id)
    folder_id = str(seed_items["folder"].id)

    resp_att_file = client.post("/api/v1/tags/attach", headers=auth_headers, json={"tag_id": tag_id, "file_id": file_id})
    assert resp_att_file.status_code == 200

    resp_att_folder = client.post("/api/v1/tags/attach", headers=auth_headers, json={"tag_id": tag_id, "folder_id": folder_id})
    assert resp_att_folder.status_code == 200

    resp_items = client.get(f"/api/v1/tags/{tag_id}/items", headers=auth_headers)
    assert resp_items.status_code == 200
    data = resp_items.json()
    assert data["tag"]["item_count"] == 2
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "invoice.pdf"
    assert len(data["folders"]) == 1
    assert data["folders"][0]["name"] == "WorkDocs"

    resp_file_tags = client.get(f"/api/v1/tags/items/file/{file_id}", headers=auth_headers)
    assert resp_file_tags.status_code == 200
    assert len(resp_file_tags.json()) == 1
    assert resp_file_tags.json()[0]["name"] == "Invoices"

    resp_detach = client.post("/api/v1/tags/detach", headers=auth_headers, json={"tag_id": tag_id, "file_id": file_id})
    assert resp_detach.status_code == 200

    resp_items_after = client.get(f"/api/v1/tags/{tag_id}/items", headers=auth_headers)
    assert len(resp_items_after.json()["files"]) == 0
    assert len(resp_items_after.json()["folders"]) == 1
