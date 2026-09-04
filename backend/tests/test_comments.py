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
from app.models.share import Share, ShareRole
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
def owner_user(db_session):
    """Create file owner user."""
    user = User(
        email="owner@example.com",
        hashed_password=hash_password("OwnerPassword123!"),
        full_name="Alice Owner",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def collaborator_user(db_session):
    """Create collaborator user."""
    user = User(
        email="collab@example.com",
        hashed_password=hash_password("CollabPassword123!"),
        full_name="Bob Collaborator",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def stranger_user(db_session):
    """Create unrelated user."""
    user = User(
        email="stranger@example.com",
        hashed_password=hash_password("StrangerPassword123!"),
        full_name="Charlie Stranger",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_file(db_session, owner_user, collaborator_user):
    """Create test file owned by owner and shared with collaborator."""
    file = File(
        name="project_proposal.docx",
        owner_id=owner_user.id,
        folder_id=None,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=20000,
        storage_path="uploads/proposal.docx",
    )
    db_session.add(file)
    db_session.flush()

    share = Share(
        granter_id=owner_user.id,
        grantee_id=collaborator_user.id,
        file_id=file.id,
        role=ShareRole.VIEWER,
    )
    db_session.add(share)
    db_session.commit()
    return file

def test_comments_collaboration_flow(client, owner_user, collaborator_user, stranger_user, test_file):
    """Test full file comments lifecycle across multiple users."""
    owner_token = create_access_token(subject=str(owner_user.id))
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    collab_token = create_access_token(subject=str(collaborator_user.id))
    collab_headers = {"Authorization": f"Bearer {collab_token}"}

    stranger_token = create_access_token(subject=str(stranger_user.id))
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    file_id = str(test_file.id)

    resp1 = client.post(
        f"/api/v1/files/{file_id}/comments",
        headers=owner_headers,
        json={"content": "Please review Section 3."},
    )
    assert resp1.status_code == 201
    c1 = resp1.json()
    assert c1["content"] == "Please review Section 3."
    assert c1["author"]["email"] == "owner@example.com"
    assert c1["author"]["full_name"] == "Alice Owner"

    resp2 = client.post(
        f"/api/v1/files/{file_id}/comments",
        headers=collab_headers,
        json={"content": "Looks good! Left minor edits."},
    )
    assert resp2.status_code == 201
    c2 = resp2.json()
    assert c2["author"]["email"] == "collab@example.com"

    resp_unauth = client.post(
        f"/api/v1/files/{file_id}/comments",
        headers=stranger_headers,
        json={"content": "Spam comment"},
    )
    assert resp_unauth.status_code == 403

    resp_list = client.get(f"/api/v1/files/{file_id}/comments", headers=collab_headers)
    assert resp_list.status_code == 200
    comments = resp_list.json()["comments"]
    assert len(comments) == 2
    assert comments[0]["content"] == "Please review Section 3."
    assert comments[1]["content"] == "Looks good! Left minor edits."

    c2_id = c2["id"]
    resp_edit = client.put(
        f"/api/v1/files/comments/{c2_id}",
        headers=collab_headers,
        json={"content": "Looks good! Fully approved."},
    )
    assert resp_edit.status_code == 200
    assert resp_edit.json()["content"] == "Looks good! Fully approved."

    resp_del_mod = client.delete(f"/api/v1/files/comments/{c2_id}", headers=owner_headers)
    assert resp_del_mod.status_code == 204

    resp_final = client.get(f"/api/v1/files/{file_id}/comments", headers=owner_headers)
    assert len(resp_final.json()["comments"]) == 1
