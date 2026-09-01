"""API router for batch and bulk operations on files and folders."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.batch import (
    BatchCopyRequest,
    BatchItemSelection,
    BatchMoveRequest,
    BatchOperationResult,
    BatchStarRequest,
)
from app.services.batch_service import BatchService

router = APIRouter(prefix="/batch", tags=["Batch Operations"])


@router.post("/delete", response_model=BatchOperationResult)
def batch_delete(
    payload: BatchItemSelection,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchOperationResult:
    """Move multiple files and folders to the Trash simultaneously."""
    ip_addr = request.client.host if request.client else None
    return BatchService.batch_delete(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        folder_ids=payload.folder_ids,
        ip_address=ip_addr,
    )


@router.post("/restore", response_model=BatchOperationResult)
def batch_restore(
    payload: BatchItemSelection,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchOperationResult:
    """Restore multiple files and folders from the Trash simultaneously."""
    ip_addr = request.client.host if request.client else None
    return BatchService.batch_restore(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        folder_ids=payload.folder_ids,
        ip_address=ip_addr,
    )


@router.post("/purge", response_model=BatchOperationResult)
def batch_purge(
    payload: BatchItemSelection,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchOperationResult:
    """Permanently delete multiple files and folders and purge storage objects."""
    ip_addr = request.client.host if request.client else None
    return BatchService.batch_purge(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        folder_ids=payload.folder_ids,
        ip_address=ip_addr,
    )


@router.post("/move", response_model=BatchOperationResult)
def batch_move(
    payload: BatchMoveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchOperationResult:
    """Move multiple files and folders to a target destination folder."""
    ip_addr = request.client.host if request.client else None
    return BatchService.batch_move(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        folder_ids=payload.folder_ids,
        destination_folder_id=payload.destination_folder_id,
        ip_address=ip_addr,
    )


@router.post("/copy", response_model=BatchOperationResult)
def batch_copy(
    payload: BatchCopyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchOperationResult:
    """Duplicate multiple files to a target destination folder."""
    ip_addr = request.client.host if request.client else None
    return BatchService.batch_copy(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        destination_folder_id=payload.destination_folder_id,
        ip_address=ip_addr,
    )


@router.post("/star", response_model=BatchOperationResult)
def batch_star(
    payload: BatchStarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchOperationResult:
    """Bulk star or unstar files and folders."""
    return BatchService.batch_star(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        folder_ids=payload.folder_ids,
        is_starred=payload.is_starred,
    )


@router.post("/download")
def batch_download(
    payload: BatchItemSelection,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download multiple files and folders packed into an in-memory ZIP archive preserving hierarchy."""
    zip_buffer = BatchService.create_zip_archive(
        db=db,
        user_id=current_user.id,
        file_ids=payload.file_ids,
        folder_ids=payload.folder_ids,
    )

    headers = {
        "Content-Disposition": 'attachment; filename="archive.zip"',
        "Content-Type": "application/zip",
    }

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers=headers,
    )
