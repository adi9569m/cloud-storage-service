"""Pydantic schemas for starred/favorite items."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse


class StarToggleRequest(BaseModel):
    """Payload to toggle star bookmark for a file or folder."""

    file_id: Optional[uuid.UUID] = Field(None, description="File ID to star/unstar.")
    folder_id: Optional[uuid.UUID] = Field(None, description="Folder ID to star/unstar.")

    @model_validator(mode="after")
    def validate_single_target(self) -> "StarToggleRequest":
        """Ensure exactly one target is provided."""
        has_file = self.file_id is not None
        has_folder = self.folder_id is not None
        if has_file and has_folder:
            raise ValueError("Cannot toggle star for both a file and folder simultaneously.")
        if not has_file and not has_folder:
            raise ValueError("Must provide either file_id or folder_id to toggle star.")
        return self


class StarToggleResponse(BaseModel):
    """Response returned after toggling star state."""

    is_starred: bool
    resource_type: str
    resource_id: uuid.UUID
    message: str


class StarResponse(BaseModel):
    """Schema representing a Star record."""

    id: uuid.UUID
    user_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StarredListResponse(BaseModel):
    """Unified response containing all starred folders and files for the user."""

    folders: List[FolderResponse] = Field(default_factory=list)
    files: List[FileResponse] = Field(default_factory=list)
    total_count: int = 0
