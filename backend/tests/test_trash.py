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
from app.models.file import File
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
        email="trashuser@example.com",
        hashed_password=hash_password("TrashPassword123!"),
        full_name="Trash User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_trash_listing_and_restore_all(client, test_user):
    """Test soft-deleting items, querying /trash, and restoring all items."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    folder_res = client.post("/api/v1/folders", json={"name": "Temporary Work"}, headers=headers)
    folder_id = folder_res.json()["id"]

    file_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("draft.txt", io.BytesIO(b"Draft Text"), "text/plain")},
        headers=headers,
    )
    file_id = file_res.json()["id"]

    client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
    client.delete(f"/api/v1/files/{file_id}", headers=headers)

    trash_res = client.get("/api/v1/trash", headers=headers)
    assert trash_res.status_code == 200
    trash_data = trash_res.json()
    assert trash_data["total_count"] == 2
    assert len(trash_data["folders"]) == 1
    assert len(trash_data["files"]) == 1
    assert trash_data["folders"][0]["name"] == "Temporary Work"
    assert trash_data["files"][0]["name"] == "draft.txt"

    restore_res = client.post("/api/v1/trash/restore-all", headers=headers)
    assert restore_res.status_code == 200
    restore_data = restore_res.json()
    assert restore_data["restored_folders_count"] == 1
    assert restore_data["restored_files_count"] == 1

    empty_trash_res = client.get("/api/v1/trash", headers=headers)
    assert empty_trash_res.json()["total_count"] == 0

def test_empty_trash_permanent_purge(client, db_session, test_user):
    """Test permanently emptying trash deletes records and adjusts storage quota."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    file_bytes = b"X" * 4096
    file_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("purge_me.bin", io.BytesIO(file_bytes), "application/octet-stream")},
        headers=headers,
    )
    file_id = file_res.json()["id"]

    user = db_session.scalar(select(User).where(User.id == test_user.id))
    assert user.storage_used_bytes == 4096

    client.delete(f"/api/v1/files/{file_id}", headers=headers)

    empty_res = client.delete("/api/v1/trash/empty", headers=headers)
    assert empty_res.status_code == 200
    assert empty_res.json()["deleted_files_count"] == 1
    assert empty_res.json()["purged_bytes"] == 4096

    db_session.expire_all()
    user_after = db_session.scalar(select(User).where(User.id == test_user.id))
    assert user_after.storage_used_bytes == 0

    file_record = db_session.scalar(select(File).where(File.id == uuid.UUID(file_id)))
    assert file_record is None
