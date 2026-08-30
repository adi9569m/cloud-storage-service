"""API routes for audit trail activity logging and feeds."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.activity import ActivityListResponse
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activities", tags=["Activity & Audit Logs"])


@router.get(
    "",
    response_model=ActivityListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user activity stream",
    description="Retrieve paginated audit logs for actions performed by the current user, with optional filters.",
)
def list_user_activities(
    resource_type: Optional[str] = Query(None, description="Filter by resource type: FILE, FOLDER, SHARE, LINK_SHARE."),
    action: Optional[str] = Query(None, description="Filter by action name (e.g. FILE_UPLOAD, SHARE_GRANTED)."),
    limit: int = Query(50, ge=1, le=100, description="Page limit."),
    offset: int = Query(0, ge=0, description="Page offset."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ActivityListResponse:
    """List activity stream."""
    return ActivityService.list_user_activities(
        db=db,
        user_id=current_user.id,
        resource_type=resource_type,
        action=action,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/resource/{resource_type}/{resource_id}",
    response_model=ActivityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resource audit trail",
    description="Retrieve historical activity events specifically associated with a file or folder.",
)
def list_resource_activities(
    resource_type: str,
    resource_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100, description="Page limit."),
    offset: int = Query(0, ge=0, description="Page offset."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ActivityListResponse:
    """Get audit trail for a resource."""
    return ActivityService.list_resource_activities(
        db=db,
        user_id=current_user.id,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )
