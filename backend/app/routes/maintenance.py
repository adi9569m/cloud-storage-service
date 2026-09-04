from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.maintenance import (
    ExpiredLinksCleanupResult,
    MaintenanceCleanupRequest,
    MaintenanceCleanupResult,
    StorageSyncResult,
    SystemStatusResponse,
)
from app.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["System Maintenance & Telemetry"])

@router.post("/cleanup-trash", response_model=MaintenanceCleanupResult)
def cleanup_old_trash(
    payload: MaintenanceCleanupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MaintenanceCleanupResult:
    """Purge soft-deleted items older than retention days threshold."""
    return MaintenanceService.cleanup_old_trash(
        db=db,
        older_than_days=payload.older_than_days,
        dry_run=payload.dry_run,
    )

@router.post("/cleanup-expired-links", response_model=ExpiredLinksCleanupResult)
def cleanup_expired_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ExpiredLinksCleanupResult:
    """Deactivate public link shares that have passed their expiration timestamp."""
    return MaintenanceService.cleanup_expired_links(db=db)

@router.post("/sync-storage", response_model=StorageSyncResult)
def sync_storage_quotas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StorageSyncResult:
    """Recalculate storage metrics across all users."""
    return MaintenanceService.sync_storage_quotas(db=db)

@router.get("/system-status", response_model=SystemStatusResponse)
def get_system_status(
    db: Session = Depends(get_db),
) -> SystemStatusResponse:
    """Retrieve system health diagnostics, telemetry, and platform stats."""
    return MaintenanceService.get_system_status(db=db)
