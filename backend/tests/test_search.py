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
from app.models.folder import Folder
from app.models.star import Star
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
        email="searchuser@example.com",
        hashed_password=hash_password("SearchPass123!"),
        full_name="Search Tester",
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
def seed_data(db_session, test_user):
    """Seed folders and files across various MIME types and nesting levels."""

    f_docs = Folder(name="Documents", owner_id=test_user.id, parent_id=None)
    f_media = Folder(name="Media", owner_id=test_user.id, parent_id=None)
    db_session.add_all([f_docs, f_media])
    db_session.flush()

    f_subdocs = Folder(name="Work", owner_id=test_user.id, parent_id=f_docs.id)
    db_session.add(f_subdocs)
    db_session.flush()

    file_pdf = File(
        name="annual_report.pdf",
        folder_id=f_docs.id,
        owner_id=test_user.id,
        mime_type="application/pdf",
        size_bytes=5000,
        storage_path="uploads/user/annual_report.pdf",
    )
    file_img = File(
        name="vacation_photo.png",
        folder_id=f_media.id,
        owner_id=test_user.id,
        mime_type="image/png",
        size_bytes=12000,
        storage_path="uploads/user/vacation_photo.png",
    )
    file_code = File(
        name="main_script.py",
        folder_id=f_subdocs.id,
        owner_id=test_user.id,
        mime_type="text/x-python",
        size_bytes=1500,
        storage_path="uploads/user/main_script.py",
    )
    file_zip = File(
        name="backup_archive.zip",
        folder_id=None,
        owner_id=test_user.id,
        mime_type="application/zip",
        size_bytes=25000,
        storage_path="uploads/user/backup_archive.zip",
    )
    db_session.add_all([file_pdf, file_img, file_code, file_zip])
    db_session.flush()

    star1 = Star(user_id=test_user.id, file_id=file_pdf.id)
    star2 = Star(user_id=test_user.id, folder_id=f_media.id)
    db_session.add_all([star1, star2])
    db_session.commit()

    return {
        "f_docs": f_docs,
        "f_media": f_media,
        "f_subdocs": f_subdocs,
        "file_pdf": file_pdf,
        "file_img": file_img,
        "file_code": file_code,
        "file_zip": file_zip,
    }

def test_search_all_items(client, auth_headers, seed_data):
    """Test unrestricted search returning all folders and files with facets."""
    resp = client.get("/api/v1/search", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 7
    assert data["facets"]["all"] == 7
    assert data["facets"]["folders"] == 3
    assert data["facets"]["files"] == 4
    assert data["facets"]["documents"] == 1
    assert data["facets"]["images"] == 1
    assert data["facets"]["code"] == 1
    assert data["facets"]["archives"] == 1

def test_search_by_query_string(client, auth_headers, seed_data):
    """Test searching by name keyword substring."""
    resp = client.get("/api/v1/search?q=report", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "annual_report.pdf"
    assert data["items"][0]["resource_type"] == "file"
    assert data["items"][0]["path"] == "/Documents/annual_report.pdf"

def test_search_filter_by_type_category(client, auth_headers, seed_data):
    """Test filtering by category type (image, code, folder)."""

    resp = client.get("/api/v1/search?type=folder", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert all(item["resource_type"] == "folder" for item in data["items"])

    resp_img = client.get("/api/v1/search?type=image", headers=auth_headers)
    assert resp_img.status_code == 200
    data_img = resp_img.json()
    assert data_img["total"] == 1
    assert data_img["items"][0]["name"] == "vacation_photo.png"

    resp_code = client.get("/api/v1/search?type=code", headers=auth_headers)
    assert resp_code.status_code == 200
    data_code = resp_code.json()
    assert data_code["total"] == 1
    assert data_code["items"][0]["name"] == "main_script.py"

def test_search_filter_by_extension_and_mime(client, auth_headers, seed_data):
    """Test filtering by specific extension and mime type."""
    resp_ext = client.get("/api/v1/search?extension=py", headers=auth_headers)
    assert resp_ext.status_code == 200
    data_ext = resp_ext.json()
    assert data_ext["total"] == 1
    assert data_ext["items"][0]["name"] == "main_script.py"

    resp_mime = client.get("/api/v1/search?mime_type=application/pdf", headers=auth_headers)
    assert resp_mime.status_code == 200
    assert resp_mime.json()["total"] == 1

def test_search_filter_by_size_range(client, auth_headers, seed_data):
    """Test filtering files by min_size and max_size."""
    resp = client.get("/api/v1/search?min_size=10000&max_size=30000", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 2
    names = {item["name"] for item in data["items"]}
    assert "vacation_photo.png" in names
    assert "backup_archive.zip" in names

def test_search_scoped_to_folder_subtree(client, auth_headers, seed_data):
    """Test scoping search to a parent folder including all nested subfolders."""
    f_docs_id = seed_data["f_docs"].id
    resp = client.get(f"/api/v1/search?folder_id={f_docs_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    names = {item["name"] for item in data["items"]}
    assert "annual_report.pdf" in names
    assert "main_script.py" in names
    assert "vacation_photo.png" not in names

def test_search_starred_filter(client, auth_headers, seed_data):
    """Test filtering only starred items."""
    resp = client.get("/api/v1/search?is_starred=true", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    names = {item["name"] for item in data["items"]}
    assert "annual_report.pdf" in names
    assert "Media" in names

def test_search_sorting_and_pagination(client, auth_headers, seed_data):
    """Test sorting by name ascending/descending and pagination."""
    resp = client.get("/api/v1/search?sort_by=name&sort_order=asc&page=1&page_size=2", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total_pages"] == 4

    assert data["items"][0]["name"] == "annual_report.pdf"
