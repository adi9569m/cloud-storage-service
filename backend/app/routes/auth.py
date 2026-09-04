from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.common import MessageResponse
from app.schemas.token import Token, TokenRefreshRequest
from app.schemas.user import (
    PasswordChange,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """Register a new user and return the newly created user profile."""
    return UserService.create_user(db=db, user_in=user_in)

@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with email and password to receive JWT access and refresh tokens.",
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user credentials and issue JWT tokens."""
    user = AuthService.authenticate(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )
    return AuthService.generate_tokens(user)

@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Provide a valid refresh token to obtain a fresh access and refresh token pair.",
)
def refresh_token(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Validate refresh token and issue new token pair."""
    return AuthService.refresh_tokens(db=db, refresh_token_str=payload.refresh_token)

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve profile details for the currently authenticated user.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the profile of the current active user."""
    return current_user

@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update display name or avatar URL for the current user.",
)
def update_current_user_profile(
    update_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Update profile attributes for the current active user."""
    return UserService.update_profile(
        db=db,
        user=current_user,
        update_in=update_in,
    )

@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change account password",
    description="Verify existing password and set a new password.",
)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Update user password after validating existing password."""
    UserService.update_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Password successfully updated.")
