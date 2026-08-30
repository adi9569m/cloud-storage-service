"""API routes for starred/favorite items."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.star import StarredListResponse, StarToggleRequest, StarToggleResponse
from app.services.star_service import StarService

router = APIRouter(prefix="/stars", tags=["Starred Items"])


@router.get(
    "",
    response_model=StarredListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all starred items",
    description="Retrieve a combined list of all favorite/starred files and folders for the current authenticated user.",
)
def list_starred(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StarredListResponse:
    """List all starred files and folders."""
    return StarService.list_starred(db=db, user_id=current_user.id)


@router.post(
    "/toggle",
    response_model=StarToggleResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle star bookmark on a file or folder",
    description="Add or remove an item from favorite bookmarks.",
)
def toggle_star(
    toggle_in: StarToggleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StarToggleResponse:
    """Toggle favorite bookmark."""
    ip_address = request.client.host if request.client else None
    return StarService.toggle_star(
        db=db,
        user_id=current_user.id,
        file_id=toggle_in.file_id,
        folder_id=toggle_in.folder_id,
        ip_address=ip_address,
    )
