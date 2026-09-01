"""Folder management API routes for directory creation, navigation, moves, cascades, and favorites."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.folder import (
    FolderContentsResponse,
    FolderCreate,
    FolderDetailResponse,
    FolderMove,
    FolderResponse,
    FolderTreeItem,
    FolderUpdate,
)
from app.services.folder_service import FolderService
from app.services.batch_service import BatchService

router = APIRouter(prefix="/folders", tags=["Folders"])


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a folder",
    description="Create a new directory at the root level or nested within an existing parent folder.",
)
def create_folder(
    folder_in: FolderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderResponse:
    """Create a new folder record."""
    ip_address = request.client.host if request.client else None
    folder = FolderService.create_folder(
        db=db,
        user_id=current_user.id,
        folder_in=folder_in,
        ip_address=ip_address,
    )
    is_starred = FolderService.is_folder_starred(db=db, folder_id=folder.id, user_id=current_user.id)
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=folder.owner_id,
        color=folder.color,
        is_deleted=folder.is_deleted,
        deleted_at=folder.deleted_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        is_starred=is_starred,
    )


@router.get(
    "",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List root directory contents",
    description="Retrieve all top-level active subfolders and files located at the Root storage level.",
)
def list_root_contents(
    sort_by: str = Query("name", enum=["name", "created_at", "updated_at", "size"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderContentsResponse:
    """List Root directory items."""
    return FolderService.get_folder_contents(
        db=db,
        user_id=current_user.id,
        folder_id=None,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/tree",
    response_model=List[FolderTreeItem],
    status_code=status.HTTP_200_OK,
    summary="Get full folder directory tree",
    description="Fetch the complete nested directory hierarchy tree for navigation menus and destination selectors.",
)
def get_folder_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FolderTreeItem]:
    """Retrieve recursive folder tree hierarchy."""
    return FolderService.get_folder_tree(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{folder_id}",
    response_model=FolderDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get folder details",
    description="Retrieve metadata, breadcrumb navigation trail, child item counts, and favorite status for a folder.",
)
def get_folder_detail(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderDetailResponse:
    """Get single folder details and breadcrumbs."""
    return FolderService.get_folder_detail(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
    )


@router.get(
    "/{folder_id}/contents",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List folder contents",
    description="Retrieve active child subfolders, files, and full breadcrumbs for a specific folder.",
)
def get_folder_contents(
    folder_id: uuid.UUID,
    sort_by: str = Query("name", enum=["name", "created_at", "updated_at", "size"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderContentsResponse:
    """List child items in the given folder."""
    return FolderService.get_folder_contents(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.put(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update folder metadata",
    description="Rename a folder or update its UI color tag.",
)
def update_folder(
    folder_id: uuid.UUID,
    update_in: FolderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderResponse:
    """Update folder properties."""
    ip_address = request.client.host if request.client else None
    folder = FolderService.update_folder(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
        update_in=update_in,
        ip_address=ip_address,
    )
    is_starred = FolderService.is_folder_starred(db=db, folder_id=folder.id, user_id=current_user.id)
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=folder.owner_id,
        color=folder.color,
        is_deleted=folder.is_deleted,
        deleted_at=folder.deleted_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        is_starred=is_starred,
    )


@router.post(
    "/{folder_id}/move",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Move folder",
    description="Relocate a folder to a new destination parent folder or Root, preventing circular hierarchy loops.",
)
def move_folder(
    folder_id: uuid.UUID,
    move_in: FolderMove,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderResponse:
    """Move folder to new target directory."""
    ip_address = request.client.host if request.client else None
    folder = FolderService.move_folder(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
        destination_parent_id=move_in.destination_parent_id,
        ip_address=ip_address,
    )
    is_starred = FolderService.is_folder_starred(db=db, folder_id=folder.id, user_id=current_user.id)
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=folder.owner_id,
        color=folder.color,
        is_deleted=folder.is_deleted,
        deleted_at=folder.deleted_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        is_starred=is_starred,
    )


@router.post(
    "/{folder_id}/star",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Toggle folder star status",
    description="Add or remove folder from user favorites/starred list.",
)
def toggle_star_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Toggle starred status for a folder."""
    is_starred = FolderService.toggle_star(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
    )
    return {
        "folder_id": folder_id,
        "is_starred": is_starred,
        "message": "Folder starred." if is_starred else "Folder unstarred.",
    }


@router.delete(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete folder",
    description="Move a folder and all its descendant subfolders and files to the Trash.",
)
def soft_delete_folder(
    folder_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderResponse:
    """Soft-delete folder and cascade to children."""
    ip_address = request.client.host if request.client else None
    folder = FolderService.soft_delete_folder(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=folder.owner_id,
        color=folder.color,
        is_deleted=folder.is_deleted,
        deleted_at=folder.deleted_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        is_starred=False,
    )


@router.post(
    "/{folder_id}/restore",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore folder from trash",
    description="Restore a soft-deleted folder and all its descendant items from the Trash back to active state.",
)
def restore_folder(
    folder_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FolderResponse:
    """Restore folder and child contents."""
    ip_address = request.client.host if request.client else None
    folder = FolderService.restore_folder(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    is_starred = FolderService.is_folder_starred(db=db, folder_id=folder.id, user_id=current_user.id)
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=folder.owner_id,
        color=folder.color,
        is_deleted=folder.is_deleted,
        deleted_at=folder.deleted_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        is_starred=is_starred,
    )


@router.delete(
    "/{folder_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete folder",
    description="Hard delete a folder and all its contents permanently from the database.",
)
def permanent_delete_folder(
    folder_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Permanently delete folder."""
    ip_address = request.client.host if request.client else None
    FolderService.hard_delete_folder(
        db=db,
        folder_id=folder_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )


@router.get(
    "/{folder_id}/download-zip",
    summary="Download folder as ZIP",
    description="Stream an entire directory tree with all child files and nested subdirectories as a ZIP archive.",
)
def download_folder_zip(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download folder and all its contents recursively as a ZIP archive."""
    folder = FolderService.get_folder_by_id(db=db, folder_id=folder_id, user_id=current_user.id, include_deleted=False)
    zip_buffer = BatchService.create_zip_archive(
        db=db,
        user_id=current_user.id,
        file_ids=[],
        folder_ids=[folder_id],
    )
    safe_name = folder.name.replace('"', "")
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_name}.zip"',
        "Content-Type": "application/zip",
    }
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers=headers,
    )
