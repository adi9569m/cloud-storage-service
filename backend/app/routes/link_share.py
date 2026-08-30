"""API routes for public link sharing and anonymous access."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.common import MessageResponse
from app.schemas.link_share import (
    LinkShareCreate,
    LinkShareResponse,
    LinkShareUpdate,
    PublicFolderContentsResponse,
    PublicLinkAccessRequest,
    PublicLinkAccessResponse,
)
from app.services.file_service import FileService
from app.services.link_share_service import LinkShareService

# Router for authenticated link management
router = APIRouter(prefix="/links", tags=["Public Link Management"])

# Router for unauthenticated public link consumption
public_router = APIRouter(prefix="/public/links", tags=["Public Shared Links"])


# ============================================================================
# Authenticated Management Endpoints (/api/v1/links)
# ============================================================================


@router.post(
    "",
    response_model=LinkShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a public shareable link",
    description="Generate a public URL access token for a file or folder with optional password and expiry timestamp.",
)
def create_public_link(
    link_in: LinkShareCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LinkShareResponse:
    """Create a new public share link."""
    ip_address = request.client.host if request.client else None
    return LinkShareService.create_link_share(
        db=db,
        user_id=current_user.id,
        link_in=link_in,
        ip_address=ip_address,
    )


@router.get(
    "/file/{file_id}",
    response_model=List[LinkShareResponse],
    status_code=status.HTTP_200_OK,
    summary="List public links for a file",
    description="Retrieve all public share links created for a specific file (owner only).",
)
def list_file_public_links(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[LinkShareResponse]:
    """List public links for a file."""
    return LinkShareService.list_links_for_resource(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
    )


@router.get(
    "/folder/{folder_id}",
    response_model=List[LinkShareResponse],
    status_code=status.HTTP_200_OK,
    summary="List public links for a folder",
    description="Retrieve all public share links created for a specific folder (owner only).",
)
def list_folder_public_links(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[LinkShareResponse]:
    """List public links for a folder."""
    return LinkShareService.list_links_for_resource(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
    )


@router.put(
    "/{link_id}",
    response_model=LinkShareResponse,
    status_code=status.HTTP_200_OK,
    summary="Update public link settings",
    description="Modify role, set/clear password, update expiration, or toggle active status on an existing public link.",
)
def update_public_link(
    link_id: uuid.UUID,
    update_in: LinkShareUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LinkShareResponse:
    """Update public link settings."""
    ip_address = request.client.host if request.client else None
    return LinkShareService.update_link_share(
        db=db,
        link_id=link_id,
        user_id=current_user.id,
        update_in=update_in,
        ip_address=ip_address,
    )


@router.delete(
    "/{link_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke and delete a public link",
    description="Permanently delete a public share link, instantly disabling external access.",
)
def revoke_public_link(
    link_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Revoke public share link."""
    ip_address = request.client.host if request.client else None
    LinkShareService.revoke_link_share(
        db=db,
        link_id=link_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    return MessageResponse(
        message="Public share link successfully deleted.",
        detail=f"Link {link_id} has been revoked.",
    )


# ============================================================================
# Unauthenticated Public Consumer Endpoints (/api/v1/public/links)
# ============================================================================


@public_router.get(
    "/{token}",
    response_model=PublicLinkAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect public link",
    description="Inspect a public share link. If protected, returns requires_password=True until password is validated.",
)
def inspect_public_link(
    token: str,
    password: Optional[str] = Query(None, description="Optional password for protected links."),
    request: Request = None,  # type: ignore
    db: Session = Depends(get_db),
) -> PublicLinkAccessResponse:
    """Inspect and access public link metadata."""
    ip_address = request.client.host if request and request.client else None
    return LinkShareService.access_public_link(
        db=db,
        token=token,
        password=password,
        ip_address=ip_address,
    )


@public_router.post(
    "/{token}/access",
    response_model=PublicLinkAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Access protected public link with password",
    description="Submit a password payload to validate access and retrieve shared file/folder details.",
)
def access_public_link_with_password(
    token: str,
    access_in: PublicLinkAccessRequest,
    request: Request = None,  # type: ignore
    db: Session = Depends(get_db),
) -> PublicLinkAccessResponse:
    """Access password-protected public link."""
    ip_address = request.client.host if request and request.client else None
    return LinkShareService.access_public_link(
        db=db,
        token=token,
        password=access_in.password,
        ip_address=ip_address,
    )


@public_router.get(
    "/{token}/download",
    summary="Download publicly shared file",
    description="Download the binary file content directly for a public file share link.",
)
def download_public_file(
    token: str,
    password: Optional[str] = Query(None, description="Password if link is protected."),
    db: Session = Depends(get_db),
) -> Response:
    """Download public file."""
    file = LinkShareService.get_public_file(db=db, token=token, password=password)
    data, filename, mime_type = FileService.get_file_stream(db=db, file_id=file.id, user_id=file.owner_id)

    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@public_router.get(
    "/{token}/contents",
    response_model=PublicFolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Browse public folder contents",
    description="Browse active subfolders and files inside a publicly shared folder hierarchy.",
)
def get_public_folder_contents(
    token: str,
    folder_id: Optional[uuid.UUID] = Query(None, description="Subfolder ID to navigate into."),
    password: Optional[str] = Query(None, description="Password if folder is protected."),
    db: Session = Depends(get_db),
) -> PublicFolderContentsResponse:
    """Browse public folder contents."""
    return LinkShareService.get_public_folder_contents(
        db=db,
        token=token,
        folder_id=folder_id,
        password=password,
    )
