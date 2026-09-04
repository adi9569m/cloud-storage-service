from datetime import timedelta
import uuid
import pytest
import jwt
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

def test_password_hashing():
    """Verify that password hashing and verification function correctly."""
    password = "SuperSecretPassword123!"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    assert hashed1 != hashed2
    assert hashed1 != password

    assert verify_password(password, hashed1) is True
    assert verify_password(password, hashed2) is True

    assert verify_password("WrongPassword123!", hashed1) is False
    assert verify_password("", hashed1) is False

def test_jwt_access_token_creation_and_decoding():
    """Verify access token creation, claims, and decoding."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, extra_claims={"role": "admin"})

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload

def test_jwt_refresh_token_creation_and_decoding():
    """Verify refresh token creation and claims."""
    user_id = uuid.uuid4()
    token = create_refresh_token(subject=user_id)

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert payload["exp"] > payload["iat"]

def test_jwt_token_expiration():
    """Verify that expired tokens raise jwt.ExpiredSignatureError."""
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)

def test_jwt_invalid_token():
    """Verify that malformed or tampered tokens raise jwt.InvalidTokenError."""
    with pytest.raises(jwt.InvalidTokenError):
        decode_token("not.a.valid.jwt.token")
