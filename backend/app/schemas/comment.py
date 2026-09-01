"""Pydantic schemas for file comments, replies, and collaboration."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    """Schema for posting a new comment on a file."""

    content: str = Field(..., min_length=1, description="Comment text content")


class CommentUpdate(BaseModel):
    """Schema for editing an existing comment."""

    content: str = Field(..., min_length=1, description="Updated comment text content")


class CommentAuthor(BaseModel):
    """Public author profile summary attached to comments."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class CommentResponse(BaseModel):
    """Comment entity response including author metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    author: CommentAuthor
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    """List of comments on a file with total count."""

    comments: List[CommentResponse]
    total: int
