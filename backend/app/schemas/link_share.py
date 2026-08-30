"""Pydantic schemas for public tokenized link sharing."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.share import ShareRole
from app.schemas.common import BreadcrumbItem
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse


class LinkShareCreate(BaseModel):
    """Schema for generating a public shareable link."""

    file_id: Optional[uuid.UUID] = Field(None, description="Target file ID.")
    folder_id: Optional[uuid.UUID] = Field(None, description="Target folder ID.")
    role: ShareRole = Field(default=ShareRole.VIEWER, description="Permissions granted by link: VIEWER or EDITOR.")
    password: Optional[str] = Field(None, min_length=4, max_length=100, description="Optional access password.")
    expires_at: Optional[datetime] = Field(None, description="Optional link expiration timestamp (UTC).")

    @model_validator(mode="after")
    def validate_single_target(self) -> "LinkShareCreate":
        """Ensure exactly one target resource is supplied."""
        has_file = self.file_id is not None
        has_folder = self.folder_id is not None
        if has_file and has_folder:
            raise ValueError("Cannot share both a file and a folder in the same link.")
        if not has_file and not has_folder:
            raise ValueError("Must provide either file_id or folder_id for public link.")
        return self


class LinkShareUpdate(BaseModel):
    """Schema for modifying public link settings."""

    role: Optional[ShareRole] = Field(None, description="Updated role: VIEWER or EDITOR.")
    password: Optional[str] = Field(None, min_length=4, max_length=100, description="Set or change password.")
    clear_password: Optional[bool] = Field(False, description="Set to true to remove password protection.")
    expires_at: Optional[datetime] = Field(None, description="New expiration timestamp or null.")
    is_active: Optional[bool] = Field(None, description="Toggle active state of the public link.")


class LinkShareResponse(BaseModel):
    """Public link metadata schema."""

    id: uuid.UUID
    token: str
    created_by_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    role: ShareRole
    has_password: bool = False
    expires_at: Optional[datetime] = None
    is_active: bool
    access_count: int = 0
    share_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicLinkAccessRequest(BaseModel):
    """Payload to access a password-protected public link."""

    password: Optional[str] = Field(None, description="Password if required by the link.")


class PublicLinkAccessResponse(BaseModel):
    """Response returned when consuming/inspecting a public link."""

    token: str
    role: ShareRole
    resource_type: str = Field(..., description="'file' or 'folder'")
    has_password: bool = False
    requires_password: bool = False
    file: Optional[FileResponse] = None
    folder: Optional[FolderResponse] = None
    download_url: Optional[str] = None


class PublicFolderContentsResponse(BaseModel):
    """Listing response for public folder navigation."""

    folder: FolderResponse
    breadcrumbs: List[BreadcrumbItem] = Field(default_factory=list)
    folders: List[FolderResponse] = Field(default_factory=list)
    files: List[FileResponse] = Field(default_factory=list)
    total_folders: int = 0
    total_files: int = 0
