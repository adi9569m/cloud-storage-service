import io
import uuid
import zipfile
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
        email="previewuser@example.com",
        hashed_password=hash_password("PreviewPass123!"),
        full_name="Preview User",
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
def seed_preview_data(db_session, test_user):
    """Seed test files for previewing."""
    folder = Folder(name="ProjectFolder", owner_id=test_user.id)
    db_session.add(folder)
    db_session.flush()

    video_bytes = b"0123456789" * 100
    file_video = File(
        name="sample_video.mp4",
        owner_id=test_user.id,
        folder_id=folder.id,
        mime_type="video/mp4",
        size_bytes=len(video_bytes),
        storage_path="uploads/preview/sample_video.mp4",
    )
    StorageService.save_file_bytes("uploads/preview/sample_video.mp4", video_bytes)

    text_content = "def hello_world():\n    print('Hello, world!')\n    return True\n"
    text_bytes = text_content.encode("utf-8")
    file_code = File(
        name="app.py",
        owner_id=test_user.id,
        folder_id=folder.id,
        mime_type="text/x-python",
        size_bytes=len(text_bytes),
        storage_path="uploads/preview/app.py",
    )
    StorageService.save_file_bytes("uploads/preview/app.py", text_bytes)

    db_session.add_all([file_video, file_code])
    db_session.commit()

    return {
        "folder": folder,
        "video": file_video,
        "code": file_code,
        "video_bytes": video_bytes,
        "text_content": text_content,
    }

def test_file_preview_full_stream(client, auth_headers, seed_preview_data):
    """Test standard inline preview streaming returning 200 and inline Content-Disposition."""
    vid_id = seed_preview_data["video"].id
    resp = client.get(f"/api/v1/files/{vid_id}/preview", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "video/mp4"
    assert "inline" in resp.headers["content-disposition"]
    assert resp.headers["accept-ranges"] == "bytes"
    assert len(resp.content) == len(seed_preview_data["video_bytes"])

def test_file_preview_range_request(client, auth_headers, seed_preview_data):
    """Test HTTP 206 Partial Content Range request for media seek."""
    vid_id = seed_preview_data["video"].id
    headers = {**auth_headers, "Range": "bytes=0-9"}
    resp = client.get(f"/api/v1/files/{vid_id}/preview", headers=headers)
    assert resp.status_code == 206
    assert resp.headers["content-range"] == f"bytes 0-9/{len(seed_preview_data['video_bytes'])}"
    assert resp.content == b"0123456789"

def test_file_preview_invalid_range(client, auth_headers, seed_preview_data):
    """Test 416 Requested Range Not Satisfiable when range is beyond file size."""
    vid_id = seed_preview_data["video"].id
    headers = {**auth_headers, "Range": "bytes=5000-6000"}
    resp = client.get(f"/api/v1/files/{vid_id}/preview", headers=headers)
    assert resp.status_code == 416

def test_get_text_content(client, auth_headers, seed_preview_data):
    """Test extracting decoded text content, encoding, and line counts for code editor."""
    code_id = seed_preview_data["code"].id
    resp = client.get(f"/api/v1/files/{code_id}/text-content", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "app.py"
    assert data["encoding"] == "utf-8"
    assert data["line_count"] == 3
    assert "def hello_world()" in data["content"]
    assert data["is_truncated"] is False

def test_get_text_content_non_text_file_rejected(client, auth_headers, seed_preview_data):
    """Test that binary/video files are rejected by text inspection endpoint."""
    vid_id = seed_preview_data["video"].id
    resp = client.get(f"/api/v1/files/{vid_id}/text-content", headers=auth_headers)
    assert resp.status_code == 400
    assert "not a text or code document" in resp.json()["detail"]

def test_download_folder_zip(client, auth_headers, seed_preview_data):
    """Test downloading an entire folder as a recursive ZIP archive."""
    folder_id = seed_preview_data["folder"].id
    resp = client.get(f"/api/v1/folders/{folder_id}/download-zip", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "ProjectFolder.zip" in resp.headers["content-disposition"]

    zip_bytes = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        namelist = zf.namelist()
        assert "ProjectFolder/sample_video.mp4" in namelist
        assert "ProjectFolder/app.py" in namelist
