from datetime import datetime, timedelta, timezone
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
from app.models.link_share import LinkShare
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
def admin_user(db_session):
    """Create admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="System Admin",
        is_active=True,
        storage_used_bytes=50000,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(admin_user):
    """Generate bearer token headers."""
    token = create_access_token(subject=str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}

def test_trash_retention_cleanup(client, auth_headers, db_session, admin_user):
    """Test auto-purging trash items older than threshold while preserving fresh trash."""

    old_deleted_date = datetime.now(timezone.utc) - timedelta(days=45)
    old_file = File(
        name="old_trash.txt",
        owner_id=admin_user.id,
        mime_type="text/plain",
        size_bytes=1000,
        storage_path="uploads/old_trash.txt",
        is_deleted=True,
        deleted_at=old_deleted_date,
    )

    recent_deleted_date = datetime.now(timezone.utc) - timedelta(days=5)
    recent_file = File(
        name="recent_trash.txt",
        owner_id=admin_user.id,
        mime_type="text/plain",
        size_bytes=2000,
        storage_path="uploads/recent_trash.txt",
        is_deleted=True,
        deleted_at=recent_deleted_date,
    )
    db_session.add_all([old_file, recent_file])
    db_session.commit()

    resp_dry = client.post(
        "/api/v1/maintenance/cleanup-trash",
        headers=auth_headers,
        json={"older_than_days": 30, "dry_run": True},
    )
    assert resp_dry.status_code == 200
    dry_data = resp_dry.json()
    assert dry_data["purged_files_count"] == 1
    assert dry_data["dry_run"] is True
    assert dry_data["freed_bytes"] == 1000

    resp_act = client.post(
        "/api/v1/maintenance/cleanup-trash",
        headers=auth_headers,
        json={"older_than_days": 30, "dry_run": False},
    )
    assert resp_act.status_code == 200
    act_data = resp_act.json()
    assert act_data["purged_files_count"] == 1
    assert act_data["dry_run"] is False

    assert db_session.get(File, old_file.id) is None
    assert db_session.get(File, recent_file.id) is not None

def test_expired_links_cleanup(client, auth_headers, db_session, admin_user):
    """Test deactivating expired public links."""
    file = File(
        name="test_link_file.txt",
        owner_id=admin_user.id,
        mime_type="text/plain",
        size_bytes=500,
        storage_path="uploads/test_link_file.txt",
    )
    db_session.add(file)
    db_session.flush()

    past_date = datetime.now(timezone.utc) - timedelta(days=2)
    expired_link = LinkShare(
        token="expired_token_123",
        created_by_id=admin_user.id,
        file_id=file.id,
        is_active=True,
        expires_at=past_date,
    )
    db_session.add(expired_link)
    db_session.commit()

    resp = client.post("/api/v1/maintenance/cleanup-expired-links", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["deactivated_links_count"] == 1

    db_session.refresh(expired_link)
    assert expired_link.is_active is False

def test_system_status_endpoint(client, db_session, admin_user):
    """Test retrieving system health diagnostics."""
    resp = client.get("/api/v1/maintenance/system-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["total_users"] == 1
