"""Comment service managing file collaboration, comment threads, and permissions."""

from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.file import File
from app.models.share import Share
from app.models.user import User
from app.schemas.comment import (
    CommentAuthor,
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from app.services.activity_service import ActivityService


class CommentService:
    """Service providing collaboration comment operations on files."""

    @classmethod
    def _verify_file_access(cls, db: Session, file_id: uuid.UUID, user_id: uuid.UUID) -> File:
        """Verify user is owner or has received a direct or parent folder share."""
        file = db.scalars(
            select(File).where(File.id == file_id, File.is_deleted.is_(False))
        ).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            )

        if file.owner_id == user_id:
            return file

        # Check share
        share = db.scalars(
            select(Share).where(
                Share.grantee_id == user_id,
                (Share.file_id == file_id) | (Share.folder_id == file.folder_id),
            )
        ).first()

        if not share:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access or comment on this file.",
            )

        return file

    @classmethod
    def _to_comment_response(cls, db: Session, comment: Comment) -> CommentResponse:
        """Helper to convert Comment model to CommentResponse schema with author profile."""
        user = db.get(User, comment.user_id)
        author = CommentAuthor(
            id=comment.user_id,
            email=user.email if user else "unknown@example.com",
            full_name=user.full_name if user else None,
            avatar_url=user.avatar_url if user else None,
        )

        return CommentResponse(
            id=comment.id,
            file_id=comment.file_id,
            user_id=comment.user_id,
            content=comment.content,
            author=author,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    @classmethod
    def create_comment(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        comment_in: CommentCreate,
        ip_address: Optional[str] = None,
    ) -> CommentResponse:
        """Create and persist a new collaboration comment on a file."""
        file = cls._verify_file_access(db=db, file_id=file_id, user_id=user_id)

        comment = Comment(
            file_id=file.id,
            user_id=user_id,
            content=comment_in.content.strip(),
        )
        db.add(comment)
        db.flush()

        ActivityService.log_activity(
            db=db,
            action="FILE_COMMENT_ADD",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"comment_id": str(comment.id), "file_name": file.name},
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(comment)
        return cls._to_comment_response(db=db, comment=comment)

    @classmethod
    def list_comments(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CommentListResponse:
        """Retrieve all comments on a file in chronological order."""
        cls._verify_file_access(db=db, file_id=file_id, user_id=user_id)

        comments = db.scalars(
            select(Comment).where(Comment.file_id == file_id).order_by(Comment.created_at.asc())
        ).all()

        comment_responses = [cls._to_comment_response(db=db, comment=c) for c in comments]
        return CommentListResponse(
            comments=comment_responses,
            total=len(comment_responses),
        )

    @classmethod
    def update_comment(
        cls,
        db: Session,
        comment_id: uuid.UUID,
        user_id: uuid.UUID,
        comment_in: CommentUpdate,
    ) -> CommentResponse:
        """Edit an existing comment (author only)."""
        comment = db.get(Comment, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found.",
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments.",
            )

        comment.content = comment_in.content.strip()
        db.commit()
        db.refresh(comment)
        return cls._to_comment_response(db=db, comment=comment)

    @classmethod
    def delete_comment(
        cls,
        db: Session,
        comment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Delete a comment (author or file owner)."""
        comment = db.get(Comment, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found.",
            )

        file = db.get(File, comment.file_id)
        is_file_owner = file and file.owner_id == user_id
        is_comment_author = comment.user_id == user_id

        if not is_comment_author and not is_file_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this comment.",
            )

        db.delete(comment)
        db.commit()
