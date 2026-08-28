"""Pydantic schemas for file entities and responses."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FileBase(BaseModel):
    """Base schema for file attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="File name including extension.")
    mime_type: str = Field(..., max_length=127, description="MIME type format.")


class FileResponse(BaseModel):
    """File metadata response schema."""

    id: uuid.UUID
    name: str
    folder_id: uuid.UUID | None
    owner_id: uuid.UUID
    mime_type: str
    size_bytes: int
    storage_path: str
    is_deleted: bool
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    is_starred: bool = False

    model_config = ConfigDict(from_attributes=True)
