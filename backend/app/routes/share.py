"""API routes for user-to-user sharing and role-based access control."""

from typing import List
import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.common import MessageResponse
from app.schemas.share import (
    ShareCreate,
    SharedByMeResponse,
    SharedWithMeResponse,
    ShareResponse,
    ShareUpdate,
)
from app.services.share_service import ShareService

router = APIRouter(prefix="/shares", tags=["Shares & Collaboration"])


@router.post(
    "",
    response_model=ShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Share file or folder with another user",
    description="Grant VIEWER or EDITOR permissions on a file or folder to a recipient identified by their registered email.",
)
def create_share(
    share_in: ShareCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ShareResponse:
    """Grant direct user-to-user access."""
    ip_address = request.client.host if request.client else None
    return ShareService.create_share(
        db=db,
        granter_id=current_user.id,
        share_in=share_in,
        ip_address=ip_address,
    )


@router.get(
    "/shared-with-me",
    response_model=SharedWithMeResponse,
    status_code=status.HTTP_200_OK,
    summary="List items shared with current user",
    description="Retrieve all active files and folders that have been directly shared with the current authenticated user.",
)
def list_shared_with_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SharedWithMeResponse:
    """Get items shared with me."""
    return ShareService.list_shared_with_me(db=db, user_id=current_user.id)


@router.get(
    "/shared-by-me",
    response_model=SharedByMeResponse,
    status_code=status.HTTP_200_OK,
    summary="List shares created by current user",
    description="Retrieve all active direct shares that the current user has granted to others.",
)
def list_shared_by_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SharedByMeResponse:
    """Get shares granted by me."""
    return ShareService.list_shared_by_me(db=db, user_id=current_user.id)


@router.get(
    "/file/{file_id}",
    response_model=List[ShareResponse],
    status_code=status.HTTP_200_OK,
    summary="List shares on a file",
    description="Retrieve all direct user shares configured for a specific file (owner only).",
)
def list_file_shares(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[ShareResponse]:
    """List shares for a file."""
    return ShareService.list_shares_for_resource(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
    )


@router.get(
    "/folder/{folder_id}",
    response_model=List[ShareResponse],
    status_code=status.HTTP_200_OK,
    summary="List shares on a folder",
    description="Retrieve all direct user shares configured for a specific folder (owner only).",
)
def list_folder_shares(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[ShareResponse]:
    """List shares for a folder."""
    return ShareService.list_shares_for_resource(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
    )


@router.put(
    "/{share_id}",
    response_model=ShareResponse,
    status_code=status.HTTP_200_OK,
    summary="Update share role permission",
    description="Modify the access role (e.g. VIEWER to EDITOR or vice-versa) for an existing share record.",
)
def update_share_role(
    share_id: uuid.UUID,
    share_update: ShareUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ShareResponse:
    """Update share permission role."""
    ip_address = request.client.host if request.client else None
    return ShareService.update_share(
        db=db,
        share_id=share_id,
        user_id=current_user.id,
        share_update=share_update,
        ip_address=ip_address,
    )


@router.delete(
    "/{share_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a share",
    description="Revoke direct access to a shared file or folder. Can be performed by either the granter or grantee.",
)
def revoke_share(
    share_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Revoke/delete a share."""
    ip_address = request.client.host if request.client else None
    ShareService.revoke_share(
        db=db,
        share_id=share_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    return MessageResponse(
        message="Share permission successfully revoked.",
        detail=f"Share {share_id} has been deleted.",
    )
