from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse

class TagBase(BaseModel):
    """Base tag schema with name and UI color."""

    name: str = Field(..., min_length=1, max_length=50, description="Tag label name")
    color: str = Field("#3B82F6", max_length=30, description="Hex/CSS color code (e.g. #EF4444, #10B981)")

class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass

class TagUpdate(BaseModel):
    """Schema for updating tag name or color."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=30)

class TagResponse(TagBase):
    """Tag entity response with usage item count."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    item_count: int = Field(0, description="Number of files and folders labeled with this tag")
    created_at: datetime
    updated_at: datetime

class TagAttachRequest(BaseModel):
    """Request payload to attach a tag to a file or folder."""

    tag_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None

class TagDetachRequest(BaseModel):
    """Request payload to detach a tag from a file or folder."""

    tag_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None

class TaggedItemsResponse(BaseModel):
    """Response containing all files and folders attached to a tag."""

    tag: TagResponse
    files: List[FileResponse]
    folders: List[FolderResponse]
