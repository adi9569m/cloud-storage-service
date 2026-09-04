from typing import List
import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from app.services.comment_service import CommentService

router = APIRouter(prefix="/files", tags=["File Comments & Collaboration"])

@router.post("/{file_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_file_comment(
    file_id: uuid.UUID,
    comment_in: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CommentResponse:
    """Post a collaboration comment on a file."""
    ip_addr = request.client.host if request.client else None
    return CommentService.create_comment(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        comment_in=comment_in,
        ip_address=ip_addr,
    )

@router.get("/{file_id}/comments", response_model=CommentListResponse)
def list_file_comments(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CommentListResponse:
    """List all comments on a file in chronological order."""
    return CommentService.list_comments(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )

@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: uuid.UUID,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CommentResponse:
    """Edit an existing comment (author only)."""
    return CommentService.update_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user.id,
        comment_in=comment_in,
    )

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a comment (author or file owner)."""
    CommentService.delete_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user.id,
    )
