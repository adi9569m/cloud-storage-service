from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    """Service class for user record management."""

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Retrieve a user by primary key UUID."""
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Retrieve a user by email address (case-insensitive)."""
        normalized_email = email.lower().strip()
        stmt = select(User).where(User.email == normalized_email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user account."""
        normalized_email = user_in.email.lower().strip()
        existing = UserService.get_by_email(db, normalized_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        hashed = hash_password(user_in.password)
        user = User(
            email=normalized_email,
            hashed_password=hashed,
            full_name=user_in.full_name,
            is_active=True,
            is_verified=False,
            storage_used_bytes=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_profile(db: Session, user: User, update_in: UserUpdate) -> User:
        """Update profile metadata such as full name or avatar URL."""
        if update_in.full_name is not None:
            user.full_name = update_in.full_name
        if update_in.avatar_url is not None:
            user.avatar_url = update_in.avatar_url

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(
        db: Session, user: User, current_password: str, new_password: str
    ) -> User:
        """Change user password after verifying current credentials."""
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password verification failed.",
            )

        user.hashed_password = hash_password(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
