"""Pydantic schemas for folder entities, breadcrumbs, hierarchy trees, and responses."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.file import FileResponse


class BreadcrumbItem(BaseModel):
    """Breadcrumb trail entry representing hierarchical folder navigation."""

    id: Optional[uuid.UUID] = Field(None, description="Folder UUID. None indicates Root.")
    name: str = Field(..., description="Folder display name or 'My Drive' for Root.")

    model_config = ConfigDict(from_attributes=True)


class FolderBase(BaseModel):
    """Base folder schema with shared attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="Folder display name.")
    color: Optional[str] = Field(None, max_length=30, description="UI accent color tag.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Ensure folder name is not empty or composed solely of whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Folder name cannot be empty or whitespace only.")
        if "/" in stripped or "\\" in stripped:
            raise ValueError("Folder name cannot contain path separators ('/' or '\\').")
        return stripped


class FolderCreate(FolderBase):
    """Schema for creating a new folder."""

    parent_id: Optional[uuid.UUID] = Field(
        None,
        description="Parent folder UUID. Omit or pass null for root level.",
    )


class FolderUpdate(BaseModel):
    """Schema for updating folder metadata (rename or color change)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New folder name.")
    color: Optional[str] = Field(None, max_length=30, description="New UI accent color.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        """Validate name if provided."""
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Folder name cannot be empty or whitespace only.")
        if "/" in stripped or "\\" in stripped:
            raise ValueError("Folder name cannot contain path separators ('/' or '\\').")
        return stripped


class FolderMove(BaseModel):
    """Schema for moving a folder to a target destination folder."""

    destination_parent_id: Optional[uuid.UUID] = Field(
        None,
        description="Target destination folder UUID. Pass null to move to Root.",
    )


class FolderResponse(BaseModel):
    """Folder metadata representation."""

    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    owner_id: uuid.UUID
    color: Optional[str] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_starred: bool = False

    model_config = ConfigDict(from_attributes=True)


class FolderDetailResponse(FolderResponse):
    """Detailed folder view including breadcrumbs path and aggregate counts."""

    breadcrumbs: List[BreadcrumbItem] = Field(default_factory=list)
    subfolders_count: int = 0
    files_count: int = 0


class FolderTreeItem(BaseModel):
    """Recursive tree item for folder navigation sidebar and picker."""

    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None
    color: Optional[str] = None
    children: List["FolderTreeItem"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FolderContentsResponse(BaseModel):
    """Listing response containing breadcrumbs, child folders, and files."""

    current_folder: Optional[FolderResponse] = Field(
        None,
        description="Current folder details. Null if viewing Root directory.",
    )
    breadcrumbs: List[BreadcrumbItem] = Field(
        default_factory=list,
        description="Breadcrumb navigation trail from Root to current directory.",
    )
    folders: List[FolderResponse] = Field(
        default_factory=list,
        description="List of active child subfolders.",
    )
    files: List[FileResponse] = Field(
        default_factory=list,
        description="List of active files within this directory.",
    )
    total_folders: int = Field(0, description="Total number of immediate subfolders.")
    total_files: int = Field(0, description="Total number of immediate files.")
