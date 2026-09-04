import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.activity import Activity
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.folder import Folder
from app.models.star import Star
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

def test_direct_upload_file_root(client, auth_headers, test_user, db_session):
    """Test direct multipart file upload at Root directory."""
    file_content = b"Sample direct file upload binary content."
    files = {"file": ("document.pdf", io.BytesIO(file_content), "application/pdf")}

    response = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "document.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["size_bytes"] == len(file_content)
    assert data["folder_id"] is None
    assert data["owner_id"] == str(test_user.id)
    assert data["is_deleted"] is False
    assert data["current_version_number"] == 1

    file_id = uuid.UUID(data["id"])
    file_orm = db_session.get(File, file_id)
    assert file_orm is not None
    assert len(file_orm.versions) == 1
    assert file_orm.versions[0].version_number == 1
    assert file_orm.versions[0].size_bytes == len(file_content)

    db_session.refresh(test_user)
    assert test_user.storage_used_bytes == len(file_content)

    act = db_session.scalars(
        select(Activity).where(Activity.user_id == test_user.id, Activity.action == "FILE_UPLOAD")
    ).first()
    assert act is not None
    assert act.resource_type == "FILE"

def test_direct_upload_file_in_folder(client, auth_headers, test_user, db_session):
    """Test direct multipart upload inside a parent folder."""

    folder_resp = client.post(
        "/api/v1/folders",
        headers=auth_headers,
        json={"name": "Projects", "color": "blue"},
    )
    assert folder_resp.status_code == 201
    folder_id = folder_resp.json()["id"]

    file_content = b"Projects spec sheet"
    files = {"file": ("spec.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"folder_id": folder_id}

    response = client.post("/api/v1/files/upload", headers=auth_headers, files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "spec.docx"
    assert res_data["folder_id"] == folder_id

def test_direct_upload_duplicate_name_conflict(client, auth_headers):
    """Test duplicate file name conflict in the same directory."""
    file_content = b"first upload"
    files = {"file": ("notes.txt", io.BytesIO(file_content), "text/plain")}

    resp1 = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    assert resp1.status_code == 201

    files2 = {"file": ("notes.txt", io.BytesIO(b"second upload"), "text/plain")}
    resp2 = client.post("/api/v1/files/upload", headers=auth_headers, files=files2)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]

def test_direct_upload_invalid_folder(client, auth_headers):
    """Test uploading to a non-existent folder returns 404."""
    random_folder_id = str(uuid.uuid4())
    files = {"file": ("test.txt", io.BytesIO(b"data"), "text/plain")}
    data = {"folder_id": random_folder_id}

    resp = client.post("/api/v1/files/upload", headers=auth_headers, files=files, data=data)
    assert resp.status_code == 404

def test_presigned_init_and_complete_upload(client, auth_headers, test_user, db_session):
    """Test 2-step presigned upload initiation and completion lifecycle."""

    init_payload = {
        "name": "large_archive.zip",
        "mime_type": "application/zip",
        "size_bytes": 10485760,
        "folder_id": None,
    }
    init_resp = client.post("/api/v1/files/init-upload", headers=auth_headers, json=init_payload)
    assert init_resp.status_code == 201
    init_data = init_resp.json()
    assert "upload_url" in init_data
    assert init_data["version_number"] == 1
    assert "large_archive.zip" in init_data["storage_path"]
    file_id = init_data["file_id"]

    complete_payload = {
        "file_id": file_id,
        "version_number": 1,
        "checksum_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "actual_size_bytes": 10485760,
    }
    comp_resp = client.post("/api/v1/files/complete-upload", headers=auth_headers, json=complete_payload)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["id"] == file_id
    assert comp_data["name"] == "large_archive.zip"
    assert comp_data["size_bytes"] == 10485760

    ver1 = db_session.scalars(
        select(FileVersion).where(FileVersion.file_id == uuid.UUID(file_id))
    ).first()
    assert ver1 is not None
    assert ver1.version_number == 1
    assert ver1.checksum_sha256 == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

def test_presigned_init_duplicate_conflict(client, auth_headers):
    """Test presigned init upload duplicate file name conflict."""
    payload = {
        "name": "data.csv",
        "mime_type": "text/csv",
        "size_bytes": 500,
    }
    r1 = client.post("/api/v1/files/init-upload", headers=auth_headers, json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/files/init-upload", headers=auth_headers, json=payload)
    assert r2.status_code == 409

def test_file_versioning_direct_upload(client, auth_headers, test_user, db_session):
    """Test adding multiple versions directly via multipart upload."""

    v1_content = b"Version 1 content"
    files = {"file": ("report.pdf", io.BytesIO(v1_content), "application/pdf")}
    r1 = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    assert r1.status_code == 201
    file_id = r1.json()["id"]

    v2_content = b"Version 2 updated content with more details"
    files2 = {"file": ("report_v2.pdf", io.BytesIO(v2_content), "application/pdf")}
    r2 = client.post(f"/api/v1/files/{file_id}/versions/upload", headers=auth_headers, files=files2)
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["current_version_number"] == 2
    assert data2["size_bytes"] == len(v2_content)

    v3_content = b"Version 3 final content"
    files3 = {"file": ("report_v3.pdf", io.BytesIO(v3_content), "application/pdf")}
    r3 = client.post(f"/api/v1/files/{file_id}/versions/upload", headers=auth_headers, files=files3)
    assert r3.status_code == 201
    data3 = r3.json()
    assert data3["current_version_number"] == 3

    v_resp = client.get(f"/api/v1/files/{file_id}/versions", headers=auth_headers)
    assert v_resp.status_code == 200
    versions = v_resp.json()
    assert len(versions) == 3
    assert versions[0]["version_number"] == 3
    assert versions[1]["version_number"] == 2
    assert versions[2]["version_number"] == 1

def test_file_versioning_presigned_flow(client, auth_headers):
    """Test adding new versions via presigned init and complete endpoints."""

    files = {"file": ("contract.pdf", io.BytesIO(b"v1"), "application/pdf")}
    init_file = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = init_file.json()["id"]

    v_init = client.post(
        f"/api/v1/files/{file_id}/versions/init-upload",
        headers=auth_headers,
        json={"size_bytes": 2048},
    )
    assert v_init.status_code == 201
    assert v_init.json()["version_number"] == 2

    v_comp = client.post(
        f"/api/v1/files/{file_id}/versions/complete-upload",
        headers=auth_headers,
        json={
            "version_number": 2,
            "checksum_sha256": "v2_checksum_hex",
            "actual_size_bytes": 2048,
        },
    )
    assert v_comp.status_code == 200
    assert v_comp.json()["current_version_number"] == 2
    assert v_comp.json()["size_bytes"] == 2048

def test_file_download_presigned_and_stream(client, auth_headers):
    """Test getting download URL and direct streaming of active version."""
    content = b"Secure downloadable content for user."
    files = {"file": ("secure_memo.pdf", io.BytesIO(content), "application/pdf")}
    upload_resp = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = upload_resp.json()["id"]

    url_resp = client.get(f"/api/v1/files/{file_id}/download-url", headers=auth_headers)
    assert url_resp.status_code == 200
    url_data = url_resp.json()
    assert "download_url" in url_data
    assert url_data["name"] == "secure_memo.pdf"

    stream_resp = client.get(f"/api/v1/files/{file_id}/download", headers=auth_headers)
    assert stream_resp.status_code == 200
    assert stream_resp.content == content
    assert stream_resp.headers["content-type"].startswith("application/pdf")
    assert 'attachment; filename="secure_memo.pdf"' in stream_resp.headers["content-disposition"]

def test_historical_version_downloads(client, auth_headers):
    """Test downloading specific historical versions."""

    v1_bytes = b"First Draft"
    f1 = client.post("/api/v1/files/upload", headers=auth_headers, files={"file": ("essay.txt", io.BytesIO(v1_bytes), "text/plain")})
    file_id = f1.json()["id"]

    v2_bytes = b"Second Revision"
    client.post(f"/api/v1/files/{file_id}/versions/upload", headers=auth_headers, files={"file": ("essay.txt", io.BytesIO(v2_bytes), "text/plain")})

    d1 = client.get(f"/api/v1/files/{file_id}/versions/1/download", headers=auth_headers)
    assert d1.status_code == 200
    assert d1.content == v1_bytes

    d2 = client.get(f"/api/v1/files/{file_id}/versions/2/download", headers=auth_headers)
    assert d2.status_code == 200
    assert d2.content == v2_bytes

    d_bad = client.get(f"/api/v1/files/{file_id}/versions/99/download", headers=auth_headers)
    assert d_bad.status_code == 404

def test_get_file_detail_and_breadcrumbs(client, auth_headers):
    """Test file detail endpoint returns full breadcrumbs and version lists."""

    p_resp = client.post("/api/v1/folders", headers=auth_headers, json={"name": "Folder A"})
    parent_id = p_resp.json()["id"]
    c_resp = client.post("/api/v1/folders", headers=auth_headers, json={"name": "Folder B", "parent_id": parent_id})
    child_id = c_resp.json()["id"]

    files = {"file": ("deep_file.txt", io.BytesIO(b"content"), "text/plain")}
    upload_resp = client.post("/api/v1/files/upload", headers=auth_headers, files=files, data={"folder_id": child_id})
    file_id = upload_resp.json()["id"]

    detail_resp = client.get(f"/api/v1/files/{file_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["name"] == "deep_file.txt"
    assert len(data["breadcrumbs"]) == 3
    assert data["breadcrumbs"][0]["name"] == "My Drive"
    assert data["breadcrumbs"][1]["name"] == "Folder A"
    assert data["breadcrumbs"][2]["name"] == "Folder B"
    assert len(data["versions"]) == 1

def test_update_file_rename(client, auth_headers):
    """Test renaming a file with conflict checks."""
    files = {"file": ("old_name.txt", io.BytesIO(b"text"), "text/plain")}
    f_resp = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = f_resp.json()["id"]

    rename_resp = client.put(f"/api/v1/files/{file_id}", headers=auth_headers, json={"name": "new_name.txt"})
    assert rename_resp.status_code == 200
    assert rename_resp.json()["name"] == "new_name.txt"

    files2 = {"file": ("collision.txt", io.BytesIO(b"text2"), "text/plain")}
    client.post("/api/v1/files/upload", headers=auth_headers, files=files2)

    dup_resp = client.put(f"/api/v1/files/{file_id}", headers=auth_headers, json={"name": "collision.txt"})
    assert dup_resp.status_code == 409

def test_move_file(client, auth_headers):
    """Test relocating file between folders and root."""

    f_resp = client.post("/api/v1/folders", headers=auth_headers, json={"name": "Destination"})
    dest_id = f_resp.json()["id"]

    files = {"file": ("movable.txt", io.BytesIO(b"text"), "text/plain")}
    up_resp = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = up_resp.json()["id"]

    move_resp = client.post(f"/api/v1/files/{file_id}/move", headers=auth_headers, json={"destination_folder_id": dest_id})
    assert move_resp.status_code == 200
    assert move_resp.json()["folder_id"] == dest_id

    move_root_resp = client.post(f"/api/v1/files/{file_id}/move", headers=auth_headers, json={"destination_folder_id": None})
    assert move_root_resp.status_code == 200
    assert move_root_resp.json()["folder_id"] is None

def test_copy_file(client, auth_headers, test_user, db_session):
    """Test cloning a file and storage bytes."""
    content = b"Original copyable content."
    files = {"file": ("source.txt", io.BytesIO(content), "text/plain")}
    up_resp = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = up_resp.json()["id"]

    copy_resp = client.post(
        f"/api/v1/files/{file_id}/copy",
        headers=auth_headers,
        json={"new_name": "source_copy.txt"},
    )
    assert copy_resp.status_code == 201
    copy_data = copy_resp.json()
    assert copy_data["id"] != file_id
    assert copy_data["name"] == "source_copy.txt"
    assert copy_data["size_bytes"] == len(content)

    copy_id = copy_data["id"]
    dl = client.get(f"/api/v1/files/{copy_id}/download", headers=auth_headers)
    assert dl.status_code == 200
    assert dl.content == content

    db_session.refresh(test_user)
    assert test_user.storage_used_bytes == len(content) * 2

def test_star_toggle_and_listing(client, auth_headers):
    """Test starring and listing favorite files."""
    files = {"file": ("starred_doc.pdf", io.BytesIO(b"data"), "application/pdf")}
    up = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = up.json()["id"]

    s1 = client.post(f"/api/v1/files/{file_id}/star", headers=auth_headers)
    assert s1.status_code == 200
    assert s1.json()["is_starred"] is True

    list_resp = client.get("/api/v1/files/starred/all", headers=auth_headers)
    assert list_resp.status_code == 200
    starred_files = list_resp.json()
    assert len(starred_files) == 1
    assert starred_files[0]["id"] == file_id
    assert starred_files[0]["is_starred"] is True

    s2 = client.post(f"/api/v1/files/{file_id}/star", headers=auth_headers)
    assert s2.status_code == 200
    assert s2.json()["is_starred"] is False

    list_resp2 = client.get("/api/v1/files/starred/all", headers=auth_headers)
    assert len(list_resp2.json()) == 0

def test_soft_delete_restore_and_trash_list(client, auth_headers):
    """Test moving file to trash and restoring it."""
    files = {"file": ("trash_me.txt", io.BytesIO(b"data"), "text/plain")}
    up = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = up.json()["id"]

    del_resp = client.delete(f"/api/v1/files/{file_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["is_deleted"] is True

    get_resp = client.get(f"/api/v1/files/{file_id}", headers=auth_headers)
    assert get_resp.status_code == 404

    trash_resp = client.get("/api/v1/files/trash/all", headers=auth_headers)
    assert trash_resp.status_code == 200
    trash_files = trash_resp.json()
    assert len(trash_files) == 1
    assert trash_files[0]["id"] == file_id

    restore_resp = client.post(f"/api/v1/files/{file_id}/restore", headers=auth_headers)
    assert restore_resp.status_code == 200
    assert restore_resp.json()["is_deleted"] is False

    get_resp2 = client.get(f"/api/v1/files/{file_id}", headers=auth_headers)
    assert get_resp2.status_code == 200

def test_permanent_delete_purges_storage_and_quota(client, auth_headers, test_user, db_session):
    """Test permanent deletion purges records and decrements quota."""
    content = b"Permanent delete test content"
    files = {"file": ("purge.txt", io.BytesIO(content), "text/plain")}
    up = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = up.json()["id"]

    db_session.refresh(test_user)
    assert test_user.storage_used_bytes == len(content)

    perm_resp = client.delete(f"/api/v1/files/{file_id}/permanent", headers=auth_headers)
    assert perm_resp.status_code == 204

    file_orm = db_session.get(File, uuid.UUID(file_id))
    assert file_orm is None

    db_session.refresh(test_user)
    assert test_user.storage_used_bytes == 0

def test_multi_tenancy_file_isolation(client, auth_headers, other_auth_headers):
    """Verify that User B cannot access, modify, download, or delete User A's files."""
    files = {"file": ("user1_secret.pdf", io.BytesIO(b"Confidential"), "application/pdf")}
    up = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = up.json()["id"]

    assert client.get(f"/api/v1/files/{file_id}", headers=other_auth_headers).status_code == 404

    assert client.get(f"/api/v1/files/{file_id}/download", headers=other_auth_headers).status_code == 404

    assert client.put(f"/api/v1/files/{file_id}", headers=other_auth_headers, json={"name": "hacked.pdf"}).status_code == 404

    assert client.delete(f"/api/v1/files/{file_id}", headers=other_auth_headers).status_code == 404

    assert client.post(f"/api/v1/files/{file_id}/star", headers=other_auth_headers).status_code == 404

def test_search_files(client, auth_headers):
    """Test searching files by keyword, MIME type, and directory."""
    client.post("/api/v1/files/upload", headers=auth_headers, files={"file": ("quarterly_earnings.pdf", io.BytesIO(b"123"), "application/pdf")})
    client.post("/api/v1/files/upload", headers=auth_headers, files={"file": ("balance_sheet.xlsx", io.BytesIO(b"456"), "application/vnd.ms-excel")})
    client.post("/api/v1/files/upload", headers=auth_headers, files={"file": ("company_logo.png", io.BytesIO(b"789"), "image/png")})

    s1 = client.get("/api/v1/files/search/query?query=earnings", headers=auth_headers)
    assert s1.status_code == 200
    assert s1.json()["total_count"] == 1
    assert s1.json()["items"][0]["name"] == "quarterly_earnings.pdf"

    s2 = client.get("/api/v1/files/search/query?mime_type=image", headers=auth_headers)
    assert s2.status_code == 200
    assert s2.json()["total_count"] == 1
    assert s2.json()["items"][0]["name"] == "company_logo.png"

    s3 = client.get("/api/v1/files/search/query", headers=auth_headers)
    assert s3.status_code == 200
    assert s3.json()["total_count"] == 3
