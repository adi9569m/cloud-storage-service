"""API router for storage metrics, usage breakdowns, and quota analytics."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.storage_analytics import (
    StorageCategoryBreakdown,
    StorageUsageSummaryResponse,
)
from app.services.storage_analytics_service import StorageAnalyticsService

router = APIRouter(prefix="/storage", tags=["Storage Analytics & Quotas"])


@router.get("/summary", response_model=StorageUsageSummaryResponse)
def get_storage_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StorageUsageSummaryResponse:
    """Retrieve full storage overview including quota, usage percent, category breakdown, and top largest files."""
    return StorageAnalyticsService.get_storage_summary(db=db, user_id=current_user.id)


@router.get("/breakdown", response_model=List[StorageCategoryBreakdown])
def get_storage_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[StorageCategoryBreakdown]:
    """Retrieve detailed storage consumption breakdown across media/file categories."""
    summary = StorageAnalyticsService.get_storage_summary(db=db, user_id=current_user.id)
    return summary.breakdown


@router.post("/recalculate")
def recalculate_storage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Force re-computation of user storage consumption from stored files."""
    new_total = StorageAnalyticsService.recalculate_user_storage(db=db, user_id=current_user.id)
    return {
        "user_id": current_user.id,
        "storage_used_bytes": new_total,
        "message": "Storage consumption recalculated successfully.",
    }
