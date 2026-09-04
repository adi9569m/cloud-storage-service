import uuid
from fastapi import HTTPException, status
import jwt
from sqlalchemy.orm import Session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.token import Token
from app.services.user_service import UserService

class AuthService:
    """Service class for user authentication and token issuance."""

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        """Authenticate user credentials and return the user entity."""
        user = UserService.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled or inactive.",
            )

        return user

    @staticmethod
    def generate_tokens(user: User) -> Token:
        """Generate access and refresh tokens for a user."""
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    @staticmethod
    def refresh_tokens(db: Session, refresh_token_str: str) -> Token:
        """Validate a refresh token and issue a fresh access & refresh token pair."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = decode_token(refresh_token_str)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise credentials_exception

        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type provided for refresh endpoint.",
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception

        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception

        user = UserService.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or deactivated.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthService.generate_tokens(user)
