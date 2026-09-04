import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
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
        email="audituser@example.com",
        hashed_password=hash_password("AuditPassword123!"),
        full_name="Audit User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def other_user(db_session):
    """Create second user."""
    user = User(
        email="otheraudit@example.com",
        hashed_password=hash_password("OtherPassword123!"),
        full_name="Other Audit User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_activity_logging_and_stream_filtering(client, test_user):
    """Test user operations record activity logs and can be filtered by action and resource type."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    folder_res = client.post("/api/v1/folders", json={"name": "Engineering"}, headers=headers)
    assert folder_res.status_code == 201
    folder_id = folder_res.json()["id"]

    file_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("design_doc.pdf", io.BytesIO(b"Architecture Doc"), "application/pdf")},
        data={"folder_id": folder_id},
        headers=headers,
    )
    assert file_res.status_code == 201
    file_id = file_res.json()["id"]

    link_res = client.post(
        "/api/v1/links",
        json={"file_id": file_id, "role": "VIEWER"},
        headers=headers,
    )
    assert link_res.status_code == 201

    stream_res = client.get("/api/v1/activities", headers=headers)
    assert stream_res.status_code == 200
    data = stream_res.json()
    assert data["total_count"] >= 3
    actions = [item["action"] for item in data["items"]]
    assert "FOLDER_CREATE" in actions
    assert "FILE_UPLOAD" in actions
    assert "LINK_SHARE_CREATED" in actions

    file_filter_res = client.get("/api/v1/activities?resource_type=FILE", headers=headers)
    assert file_filter_res.status_code == 200
    for item in file_filter_res.json()["items"]:
        assert item["resource_type"] == "FILE"

    folder_filter_res = client.get("/api/v1/activities?action=FOLDER_CREATE", headers=headers)
    assert folder_filter_res.status_code == 200
    assert len(folder_filter_res.json()["items"]) == 1
    assert folder_filter_res.json()["items"][0]["action"] == "FOLDER_CREATE"

def test_resource_audit_trail(client, test_user, other_user):
    """Test retrieving activity log for a specific resource."""
    user_token = create_access_token(subject=str(test_user.id))
    other_token = create_access_token(subject=str(other_user.id))

    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": ("contract.pdf", io.BytesIO(b"Legal Contract"), "application/pdf")},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    file_id = upload_res.json()["id"]

    client.put(
        f"/api/v1/files/{file_id}",
        json={"name": "signed_contract.pdf"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    audit_res = client.get(
        f"/api/v1/activities/resource/FILE/{file_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert data["total_count"] >= 2
    actions = [item["action"] for item in data["items"]]
    assert "FILE_UPLOAD" in actions
    assert "FILE_RENAME" in actions

    denied_res = client.get(
        f"/api/v1/activities/resource/FILE/{file_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert denied_res.status_code == 403
