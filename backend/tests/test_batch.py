"""Integration tests for Batch and Bulk Operations (move, copy, star, delete, purge, zip download)."""

import io
import uuid
import zipfile
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
        email="batchuser@example.com",
        hashed_password=hash_password("BatchPass123!"),
        full_name="Batch User",
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
def batch_seed(db_session, test_user):
    """Seed test files and folders for batch operations."""
    folder1 = Folder(name="BatchFolder1", owner_id=test_user.id)
    folder2 = Folder(name="BatchFolder2", owner_id=test_user.id)
    db_session.add_all([folder1, folder2])
    db_session.flush()

    file1 = File(
        name="file1.txt",
        owner_id=test_user.id,
        folder_id=None,
        mime_type="text/plain",
        size_bytes=100,
        storage_path="uploads/batch/file1.txt",
    )
    file2 = File(
        name="file2.txt",
        owner_id=test_user.id,
        folder_id=folder1.id,
        mime_type="text/plain",
        size_bytes=200,
        storage_path="uploads/batch/file2.txt",
    )
    db_session.add_all([file1, file2])
    db_session.commit()

    StorageService.save_file_bytes("uploads/batch/file1.txt", b"Hello from file 1")
    StorageService.save_file_bytes("uploads/batch/file2.txt", b"Hello from file 2")

    return {
        "folder1": folder1,
        "folder2": folder2,
        "file1": file1,
        "file2": file2,
    }


def test_batch_delete_and_restore(client, auth_headers, batch_seed, db_session):
    """Test bulk soft delete and subsequent bulk restore."""
    f1_id = str(batch_seed["folder1"].id)
    file1_id = str(batch_seed["file1"].id)

    # 1. Batch Delete
    payload = {"folder_ids": [f1_id], "file_ids": [file1_id]}
    resp = client.post("/api/v1/batch/delete", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_succeeded"] == 2
    assert data["total_failed"] == 0

    # Verify soft-deleted in database
    f1 = db_session.get(Folder, batch_seed["folder1"].id)
    fl1 = db_session.get(File, batch_seed["file1"].id)
    assert f1.is_deleted is True
    assert fl1.is_deleted is True

    # 2. Batch Restore
    resp_restore = client.post("/api/v1/batch/restore", headers=auth_headers, json=payload)
    assert resp_restore.status_code == 200
    data_restore = resp_restore.json()
    assert data_restore["total_succeeded"] == 2

    db_session.refresh(f1)
    db_session.refresh(fl1)
    assert f1.is_deleted is False
    assert fl1.is_deleted is False


def test_batch_move(client, auth_headers, batch_seed, db_session):
    """Test bulk moving files and folders into a destination directory."""
    f2_id = str(batch_seed["folder2"].id)
    file1_id = str(batch_seed["file1"].id)
    f1_id = str(batch_seed["folder1"].id)

    payload = {
        "folder_ids": [f1_id],
        "file_ids": [file1_id],
        "destination_folder_id": f2_id,
    }
    resp = client.post("/api/v1/batch/move", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_succeeded"] == 2

    # Verify new parents in DB
    f1 = db_session.get(Folder, batch_seed["folder1"].id)
    fl1 = db_session.get(File, batch_seed["file1"].id)
    assert f1.parent_id == batch_seed["folder2"].id
    assert fl1.folder_id == batch_seed["folder2"].id


def test_batch_copy(client, auth_headers, batch_seed, db_session):
    """Test bulk copying files into a destination directory."""
    file1_id = str(batch_seed["file1"].id)
    file2_id = str(batch_seed["file2"].id)
    f2_id = str(batch_seed["folder2"].id)

    payload = {
        "file_ids": [file1_id, file2_id],
        "destination_folder_id": f2_id,
    }
    resp = client.post("/api/v1/batch/copy", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_succeeded"] == 2

    # Check that copied files exist in Folder 2
    copied = db_session.scalars(
        select(File).where(File.folder_id == batch_seed["folder2"].id)
    ).all()
    assert len(copied) == 2


def test_batch_star_and_unstar(client, auth_headers, batch_seed, db_session):
    """Test bulk star toggle."""
    f1_id = str(batch_seed["folder1"].id)
    file1_id = str(batch_seed["file1"].id)

    # Star both
    payload = {"folder_ids": [f1_id], "file_ids": [file1_id], "is_starred": True}
    resp = client.post("/api/v1/batch/star", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    assert resp.json()["total_succeeded"] == 2

    stars = db_session.scalars(select(Star)).all()
    assert len(stars) == 2

    # Unstar both
    payload_unstar = {"folder_ids": [f1_id], "file_ids": [file1_id], "is_starred": False}
    resp_unstar = client.post("/api/v1/batch/star", headers=auth_headers, json=payload_unstar)
    assert resp_unstar.status_code == 200
    assert resp_unstar.json()["total_succeeded"] == 2

    stars_after = db_session.scalars(select(Star)).all()
    assert len(stars_after) == 0


def test_batch_download_zip(client, auth_headers, batch_seed):
    """Test batch ZIP stream creation and verify zip contents."""
    f1_id = str(batch_seed["folder1"].id)
    file1_id = str(batch_seed["file1"].id)

    payload = {"folder_ids": [f1_id], "file_ids": [file1_id]}
    resp = client.post("/api/v1/batch/download", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    # Verify ZIP integrity
    zip_bytes = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        namelist = zf.namelist()
        assert "file1.txt" in namelist
        assert "BatchFolder1/file2.txt" in namelist
        assert zf.read("file1.txt") == b"Hello from file 1"
        assert zf.read("BatchFolder1/file2.txt") == b"Hello from file 2"
