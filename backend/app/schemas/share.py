"""Pydantic schemas for direct user-to-user sharing and RBAC."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.models.share import ShareRole
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse


class ShareCreate(BaseModel):
    """Schema for granting resource access to another user by email."""

    grantee_email: EmailStr = Field(..., description="Email of recipient user to share with.")
    file_id: Optional[uuid.UUID] = Field(None, description="File UUID if sharing a file.")
    folder_id: Optional[uuid.UUID] = Field(None, description="Folder UUID if sharing a folder.")
    role: ShareRole = Field(default=ShareRole.VIEWER, description="Assigned role: VIEWER or EDITOR.")

    @model_validator(mode="after")
    def validate_single_target(self) -> "ShareCreate":
        """Ensure exactly one of file_id or folder_id is provided."""
        has_file = self.file_id is not None
        has_folder = self.folder_id is not None
        if has_file and has_folder:
            raise ValueError("Cannot share both a file and a folder in the same share request.")
        if not has_file and not has_folder:
            raise ValueError("Must provide either file_id or folder_id to share.")
        return self


class ShareUpdate(BaseModel):
    """Schema for updating an existing share's role permission."""

    role: ShareRole = Field(..., description="Updated role: VIEWER or EDITOR.")


class ShareResponse(BaseModel):
    """Schema representing a direct share record."""

    id: uuid.UUID
    granter_id: uuid.UUID
    granter_email: Optional[str] = None
    granter_name: Optional[str] = None
    grantee_id: uuid.UUID
    grantee_email: Optional[str] = None
    grantee_name: Optional[str] = None
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    role: ShareRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SharedItemResponse(BaseModel):
    """Schema representing an item shared with the current user."""

    share_id: uuid.UUID
    role: ShareRole
    resource_type: str = Field(..., description="'file' or 'folder'")
    file: Optional[FileResponse] = None
    folder: Optional[FolderResponse] = None
    shared_by_id: uuid.UUID
    shared_by_email: Optional[str] = None
    shared_by_name: Optional[str] = None
    shared_at: datetime


class SharedWithMeResponse(BaseModel):
    """Response envelope for all items shared with the current user."""

    files: List[SharedItemResponse] = Field(default_factory=list)
    folders: List[SharedItemResponse] = Field(default_factory=list)
    total_count: int = 0


class SharedByMeResponse(BaseModel):
    """Response envelope for all shares granted by the current user."""

    shares: List[ShareResponse] = Field(default_factory=list)
    total_count: int = 0
