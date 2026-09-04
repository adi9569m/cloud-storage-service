import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
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

def test_register_user_success(client):
    """Test successful user registration."""
    payload = {
        "email": "developer@example.com",
        "password": "Password123!",
        "full_name": "Test Developer",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "developer@example.com"
    assert data["full_name"] == "Test Developer"
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert data["storage_used_bytes"] == 0
    assert "hashed_password" not in data

def test_register_duplicate_email(client):
    """Test registering with an existing email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "User One",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload_dup = {
        "email": "  DUPLICATE@example.com  ",
        "password": "Password456!",
        "full_name": "User Two",
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

def test_register_validation_error(client):
    """Test registration input validation (short password and bad email format)."""

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "notanemail", "password": "ValidPassword123!"},
    )
    assert response.status_code == 422

def test_login_success(client):
    """Test successful user login returning access and refresh tokens."""
    reg_payload = {
        "email": "login_test@example.com",
        "password": "LoginPassword123!",
        "full_name": "Login User",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "login_test@example.com",
        "password": "LoginPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    """Test login failure on incorrect password."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "CorrectPassword123!"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client):
    """Test login failure for nonexistent email."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "SomePassword123!"},
    )
    assert response.status_code == 401

def test_login_inactive_user(client, db_session):
    """Test that deactivated accounts cannot log in."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("Password123!"),
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "Password123!"},
    )
    assert response.status_code == 403
    assert "disabled or inactive" in response.json()["detail"]

def test_refresh_token_flow(client):
    """Test refreshing token pair with a valid refresh token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "Password123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "Password123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_refresh_with_access_token_rejected(client):
    """Test that providing an access token to the refresh endpoint is rejected."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh_fail@example.com", "password": "Password123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_fail@example.com", "password": "Password123!"},
    )
    access_token = login_res.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 400
    assert "Invalid token type" in response.json()["detail"]

def test_get_current_user_profile(client):
    """Test fetching profile for authenticated user."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "Password123!",
            "full_name": "Me Profile",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "Password123!"},
    )
    access_token = login_res.json()["access_token"]

    res_no_auth = client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401

    res_bad_auth = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert res_bad_auth.status_code == 401

    res_valid = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me Profile"

def test_update_profile(client):
    """Test updating user display name and avatar URL."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "update_me@example.com", "password": "Password123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "update_me@example.com", "password": "Password123!"},
    )
    access_token = login_res.json()["access_token"]

    update_payload = {
        "full_name": "Updated Name",
        "avatar_url": "https://example.com/avatar.png",
    }
    response = client.put(
        "/api/v1/auth/me",
        json=update_payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["avatar_url"] == "https://example.com/avatar.png"

def test_change_password_flow(client):
    """Test password change and subsequent login with new credentials."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "pw_change@example.com", "password": "OldPassword123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "pw_change@example.com", "password": "OldPassword123!"},
    )
    access_token = login_res.json()["access_token"]

    fail_res = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongOldPassword1!", "new_password": "NewPassword123!"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert fail_res.status_code == 400
    assert "verification failed" in fail_res.json()["detail"]

    ok_res = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "OldPassword123!", "new_password": "NewPassword123!"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert ok_res.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw_change@example.com", "password": "OldPassword123!"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw_change@example.com", "password": "NewPassword123!"},
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

def test_refresh_expired_token(client):
    """Test that expired refresh token returns 401."""
    from datetime import timedelta
    from app.core.security import create_refresh_token
    import uuid

    fake_id = uuid.uuid4()
    expired_refresh = create_refresh_token(subject=fake_id, expires_delta=timedelta(seconds=-10))

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_refresh_invalid_format_token(client):
    """Test that malformed refresh token returns 401."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "malformed.refresh.token"},
    )
    assert response.status_code == 401

def test_get_me_with_expired_token(client):
    """Test that accessing /me with an expired access token returns 401."""
    from datetime import timedelta
    from app.core.security import create_access_token
    import uuid

    fake_id = uuid.uuid4()
    expired_access = create_access_token(subject=fake_id, expires_delta=timedelta(seconds=-10))

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_access}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_get_me_with_refresh_token_rejected(client):
    """Test that using a refresh token as bearer access token for /me returns 401."""
    from app.core.security import create_refresh_token
    import uuid

    fake_id = uuid.uuid4()
    refresh_tok = create_refresh_token(subject=fake_id)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_tok}"},
    )
    assert response.status_code == 401
    assert "access token required" in response.json()["detail"].lower()

def test_login_case_insensitivity(client):
    """Test that login email is case-insensitive."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "case.sensitive@example.com", "password": "Password123!"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "CASE.SENSITIVE@EXAMPLE.COM", "password": "Password123!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

