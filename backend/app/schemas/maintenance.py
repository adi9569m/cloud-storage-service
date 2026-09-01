"""Pydantic schemas for system maintenance, automated cleanup, and telemetry."""

from datetime import datetime
from pydantic import BaseModel, Field


class MaintenanceCleanupRequest(BaseModel):
    """Parameters for triggered trash cleanup."""

    older_than_days: int = Field(30, ge=1, description="Threshold age in days for trash purge")
    dry_run: bool = Field(False, description="If true, compute statistics without actually deleting items")


class MaintenanceCleanupResult(BaseModel):
    """Summary of purged trash items and reclaimed storage bytes."""

    purged_files_count: int = 0
    purged_folders_count: int = 0
    freed_bytes: int = 0
    dry_run: bool = False
    message: str = "Maintenance trash cleanup completed"


class ExpiredLinksCleanupResult(BaseModel):
    """Summary of deactivated expired public share links."""

    deactivated_links_count: int = 0
    message: str = "Expired link cleanup completed"


class StorageSyncResult(BaseModel):
    """Summary of user storage quota reconciliation."""

    users_synced: int = 0
    total_storage_bytes: int = 0
    message: str = "Storage recalculation completed"


class SystemStatusResponse(BaseModel):
    """System health diagnostics, environment configuration, and database metrics."""

    status: str = "healthy"
    environment: str
    total_users: int
    total_files: int
    total_folders: int
    total_storage_bytes: int
    rate_limiting_enabled: bool
    timestamp: datetime
