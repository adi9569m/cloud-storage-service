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
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
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
    user = User(
        email="archiveuser@example.com",
        hashed_password=hash_password("SecretPass123!"),
        full_name="Archive User",
        is_active=True,
        is_verified=True,
        storage_used_bytes=0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(test_user):
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

def create_sample_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("notes.txt", b"Hello from notes inside archive")
        zf.writestr("subfolder/inner.txt", b"Inner file content")
        zf.writestr("subfolder/nested/deep.json", b'{"status": "ok"}')
    buf.seek(0)
    return buf.getvalue()

def test_extract_zip_archive_with_nested_hierarchy(client, auth_headers, db_session, test_user):
    zip_bytes = create_sample_zip_bytes()
    upload_res = client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files={"file": ("bundle.zip", zip_bytes, "application/zip")},
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["id"]

    extract_res = client.post(
        f"/api/v1/files/{file_id}/extract",
        headers=auth_headers,
        json={"create_subfolder": True},
    )
    assert extract_res.status_code == 201
    data = extract_res.json()
    assert data["files_count"] == 3
    assert data["folders_count"] >= 2
    assert data["total_unpacked_bytes"] > 0
    assert data["extracted_folder_name"] == "bundle"

    db_files = db_session.query(File).filter(File.owner_id == test_user.id, File.is_deleted.is_(False)).all()
    filenames = [f.name for f in db_files]
    assert "bundle.zip" in filenames
    assert "notes.txt" in filenames
    assert "inner.txt" in filenames
    assert "deep.json" in filenames

def test_extract_zip_into_custom_destination(client, auth_headers, db_session, test_user):
    folder_res = client.post(
        "/api/v1/folders/",
        headers=auth_headers,
        json={"name": "TargetFolder", "parent_id": None},
    )
    assert folder_res.status_code == 201
    dest_id = folder_res.json()["id"]

    zip_bytes = create_sample_zip_bytes()
    upload_res = client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files={"file": ("project.zip", zip_bytes, "application/zip")},
    )
    file_id = upload_res.json()["id"]

    extract_res = client.post(
        f"/api/v1/files/{file_id}/extract",
        headers=auth_headers,
        json={"destination_folder_id": dest_id, "create_subfolder": False},
    )
    assert extract_res.status_code == 201
    assert extract_res.json()["destination_folder_id"] == dest_id
    assert extract_res.json()["files_count"] == 3

def test_extract_non_zip_file_rejected(client, auth_headers, test_user):
    upload_res = client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files={"file": ("plain.txt", b"plain text content", "text/plain")},
    )
    file_id = upload_res.json()["id"]

    extract_res = client.post(
        f"/api/v1/files/{file_id}/extract",
        headers=auth_headers,
        json={"create_subfolder": True},
    )
    assert extract_res.status_code == 400
    assert "not a supported ZIP" in extract_res.json()["detail"]

def test_extract_corrupted_zip_rejected(client, auth_headers, test_user):
    upload_res = client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files={"file": ("corrupt.zip", b"not-a-real-zip-content", "application/zip")},
    )
    file_id = upload_res.json()["id"]

    extract_res = client.post(
        f"/api/v1/files/{file_id}/extract",
        headers=auth_headers,
        json={"create_subfolder": True},
    )
    assert extract_res.status_code == 400
    assert "corrupted or invalid ZIP" in extract_res.json()["detail"]

def test_verify_file_checksum_endpoint(client, auth_headers, test_user):
    content = b"Data integrity verification payload"
    upload_res = client.post(
        "/api/v1/files/upload",
        headers=auth_headers,
        files={"file": ("secure.bin", content, "application/octet-stream")},
    )
    file_id = upload_res.json()["id"]

    verify_res = client.post(
        f"/api/v1/files/{file_id}/verify-checksum",
        headers=auth_headers,
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["file_id"] == file_id
    assert data["is_valid"] is True
    assert data["actual_checksum"] is not None
    assert len(data["actual_checksum"]) == 64
