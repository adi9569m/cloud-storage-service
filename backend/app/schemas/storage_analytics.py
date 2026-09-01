"""Pydantic schemas for storage analytics, metrics, and quota management."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class StorageCategoryBreakdown(BaseModel):
    """Storage usage metrics for a specific file category."""

    category: str = Field(..., description="Category name (e.g., images, documents, videos, audio, archives, code, other)")
    bytes_used: int = Field(0, description="Total storage consumed by this category in bytes")
    file_count: int = Field(0, description="Total number of files in this category")
    percentage_of_used: float = Field(0.0, description="Percentage of total used storage consumed by this category")


class StorageFileItem(BaseModel):
    """File item summary for analytics lists (e.g. largest files, recent uploads)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    size_bytes: int
    mime_type: str
    folder_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class StorageUsageSummaryResponse(BaseModel):
    """Comprehensive storage metrics, quota, breakdown, and file analytics."""

    storage_used_bytes: int = Field(..., description="Current storage used by user in bytes")
    storage_quota_bytes: int = Field(..., description="User storage quota limit in bytes")
    storage_available_bytes: int = Field(..., description="Available storage remaining in bytes")
    usage_percentage: float = Field(..., description="Percentage of storage quota utilized")
    total_files: int = Field(..., description="Total non-deleted files owned by user")
    total_folders: int = Field(..., description="Total non-deleted folders owned by user")
    total_versions: int = Field(..., description="Total file versions stored")
    trash_bytes: int = Field(0, description="Storage occupied by items currently in trash")
    breakdown: List[StorageCategoryBreakdown]
    largest_files: List[StorageFileItem]
    recent_uploads: List[StorageFileItem]
