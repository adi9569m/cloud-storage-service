"""API routes for trash listing, bulk restoration, and permanent purge."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.trash import (
    TrashEmptyResponse,
    TrashListResponse,
    TrashRestoreAllResponse,
)
from app.services.trash_service import TrashService

router = APIRouter(prefix="/trash", tags=["Trash & Recovery"])


@router.get(
    "",
    response_model=TrashListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all items in trash",
    description="Retrieve all soft-deleted folders and files residing in the Trash bin for the current user.",
)
def list_trash(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TrashListResponse:
    """List trash items."""
    return TrashService.list_trash(db=db, user_id=current_user.id)


@router.post(
    "/restore-all",
    response_model=TrashRestoreAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore all items from trash",
    description="Batch restore all soft-deleted files and folders back to active status.",
)
def restore_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TrashRestoreAllResponse:
    """Restore all trash items."""
    ip_address = request.client.host if request.client else None
    return TrashService.restore_all(
        db=db,
        user_id=current_user.id,
        ip_address=ip_address,
    )


@router.delete(
    "/empty",
    response_model=TrashEmptyResponse,
    status_code=status.HTTP_200_OK,
    summary="Permanently empty trash",
    description="Hard delete all items currently in the trash, purging physical files from cloud storage and updating quota.",
)
def empty_trash(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TrashEmptyResponse:
    """Empty trash bin."""
    ip_address = request.client.host if request.client else None
    return TrashService.empty_trash(
        db=db,
        user_id=current_user.id,
        ip_address=ip_address,
    )
