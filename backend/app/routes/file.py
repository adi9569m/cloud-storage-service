"""File management API routes for uploads, versioning, downloads, metadata, moves, copies, and stars."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File as FastAPIFile, Form, Query, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.file import (
    FileCopy,
    FileDetailResponse,
    FileDownloadResponse,
    FileListResponse,
    FileMove,
    FileResponse,
    FileUpdate,
    FileUploadComplete,
    FileUploadInit,
    FileUploadInitResponse,
    FileVersionComplete,
    FileVersionInit,
    FileVersionInitResponse,
    FileVersionResponse,
)
from app.schemas.preview import TextContentResponse
from app.services.file_service import FileService
from app.services.preview_service import PreviewService

router = APIRouter(prefix="/files", tags=["Files"])


# ============================================================================
# 1. File Uploads (Direct & Presigned)
# ============================================================================


@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Direct multipart file upload",
    description="Upload a raw file directly via multipart/form-data to create a File and FileVersion v1.",
)
async def direct_upload_file(
    request: Request,
    file: UploadFile = FastAPIFile(..., description="Binary file upload."),
    folder_id: Optional[uuid.UUID] = Form(None, description="Destination folder UUID or null for Root."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Direct multipart binary upload."""
    content = await file.read()
    ip_address = request.client.host if request.client else None
    return FileService.direct_upload(
        db=db,
        user_id=current_user.id,
        file_bytes=content,
        filename=file.filename or "uploaded_file",
        mime_type=file.content_type or "application/octet-stream",
        folder_id=folder_id,
        ip_address=ip_address,
    )


@router.post(
    "/init-upload",
    response_model=FileUploadInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate presigned upload",
    description="Reserve file metadata and obtain a time-limited presigned upload URL for direct storage transfer.",
)
def init_file_upload(
    init_in: FileUploadInit,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileUploadInitResponse:
    """Initiate presigned direct-to-storage upload."""
    ip_address = request.client.host if request.client else None
    return FileService.init_upload(
        db=db,
        user_id=current_user.id,
        init_in=init_in,
        ip_address=ip_address,
    )


@router.post(
    "/complete-upload",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete presigned upload",
    description="Notify backend that binary upload finished, finalizing metadata, registering Version 1, and updating quota.",
)
def complete_file_upload(
    complete_in: FileUploadComplete,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Finalize presigned upload."""
    ip_address = request.client.host if request.client else None
    return FileService.complete_upload(
        db=db,
        user_id=current_user.id,
        complete_in=complete_in,
        ip_address=ip_address,
    )


# ============================================================================
# 2. File Collections & Search (Fixed Paths Before Parametric Paths)
# ============================================================================


@router.get(
    "/starred/all",
    response_model=List[FileResponse],
    status_code=status.HTTP_200_OK,
    summary="List all starred files",
    description="Retrieve all favorite/starred files for the current user.",
)
def list_starred_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FileResponse]:
    """List starred files."""
    return FileService.list_starred_files(db=db, user_id=current_user.id)


@router.get(
    "/trash/all",
    response_model=List[FileResponse],
    status_code=status.HTTP_200_OK,
    summary="List all files in trash",
    description="Retrieve soft-deleted files residing in the Trash bin.",
)
def list_trash_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FileResponse]:
    """List files in trash."""
    return FileService.list_trash_files(db=db, user_id=current_user.id)


@router.get(
    "/search/query",
    response_model=FileListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search files",
    description="Search files by name substring, MIME type filter, or parent folder location.",
)
def search_files(
    query: Optional[str] = Query(None, description="Search keyword in filename."),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type pattern."),
    folder_id: Optional[uuid.UUID] = Query(None, description="Scope search to specific folder."),
    is_deleted: bool = Query(False, description="Search active (false) or trashed (true) files."),
    limit: int = Query(50, ge=1, le=100, description="Items per page."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileListResponse:
    """Search and filter user files."""
    return FileService.search_files(
        db=db,
        user_id=current_user.id,
        query=query,
        mime_type=mime_type,
        folder_id=folder_id,
        is_deleted=is_deleted,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# 3. File Versions
# ============================================================================


@router.post(
    "/{file_id}/versions/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Direct multipart version upload",
    description="Upload a new binary version directly for an existing file.",
)
async def direct_upload_version(
    file_id: uuid.UUID,
    request: Request,
    file: UploadFile = FastAPIFile(..., description="New version binary file."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Direct multipart version upload."""
    content = await file.read()
    ip_address = request.client.host if request.client else None
    return FileService.direct_upload_version(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        file_bytes=content,
        mime_type=file.content_type,
        ip_address=ip_address,
    )


@router.post(
    "/{file_id}/versions/init-upload",
    response_model=FileVersionInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate version presigned upload",
    description="Obtain presigned upload URL for uploading a new version of an existing file.",
)
def init_version_upload(
    file_id: uuid.UUID,
    version_in: FileVersionInit,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileVersionInitResponse:
    """Initiate version presigned upload."""
    ip_address = request.client.host if request.client else None
    return FileService.init_version_upload(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        version_in=version_in,
        ip_address=ip_address,
    )


@router.post(
    "/{file_id}/versions/complete-upload",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete version presigned upload",
    description="Confirm upload of new version and promote it as active version.",
)
def complete_version_upload(
    file_id: uuid.UUID,
    complete_in: FileVersionComplete,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Finalize version upload."""
    ip_address = request.client.host if request.client else None
    return FileService.complete_version_upload(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        complete_in=complete_in,
        ip_address=ip_address,
    )


@router.get(
    "/{file_id}/versions",
    response_model=List[FileVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all versions of a file",
    description="Retrieve chronological snapshot history of all uploaded versions for a file.",
)
def list_file_versions(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FileVersionResponse]:
    """List file version history."""
    return FileService.list_file_versions(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )


@router.get(
    "/{file_id}/versions/{version_number}/download-url",
    response_model=FileDownloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get download URL for specific version",
    description="Generate a presigned download URL targeting a historical version.",
)
def get_version_download_url(
    file_id: uuid.UUID,
    version_number: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileDownloadResponse:
    """Get signed download URL for specific version."""
    ip_address = request.client.host if request.client else None
    return FileService.get_download_url(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        version_number=version_number,
        ip_address=ip_address,
    )


@router.get(
    "/{file_id}/versions/{version_number}/download",
    status_code=status.HTTP_200_OK,
    summary="Direct binary download of specific version",
    description="Stream binary data of a historical version directly.",
)
def download_version_stream(
    file_id: uuid.UUID,
    version_number: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Direct stream download for historical version."""
    ip_address = request.client.host if request.client else None
    data, filename, mime_type = FileService.get_file_stream(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        version_number=version_number,
        ip_address=ip_address,
    )
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================================
# 4. File Detail, Download & Management
# ============================================================================


@router.get(
    "/{file_id}",
    response_model=FileDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get file details",
    description="Retrieve comprehensive file metadata, directory breadcrumbs, and version history list.",
)
def get_file_detail(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileDetailResponse:
    """Get file detail and breadcrumbs."""
    return FileService.get_file_detail(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )


@router.get(
    "/{file_id}/download-url",
    response_model=FileDownloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get download URL for active file",
    description="Generate a secure presigned download URL for the active file version.",
)
def get_file_download_url(
    file_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileDownloadResponse:
    """Get signed download URL for active version."""
    ip_address = request.client.host if request.client else None
    return FileService.get_download_url(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )


@router.get(
    "/{file_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Direct binary download",
    description="Stream binary data of the active file version directly.",
)
def download_file_stream(
    file_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Direct stream download for active version."""
    ip_address = request.client.host if request.client else None
    data, filename, mime_type = FileService.get_file_stream(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put(
    "/{file_id}",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update file metadata / rename",
    description="Rename a file while preventing duplicate name collisions in the same directory.",
)
def update_file(
    file_id: uuid.UUID,
    update_in: FileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Rename file."""
    ip_address = request.client.host if request.client else None
    return FileService.update_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        update_in=update_in,
        ip_address=ip_address,
    )


@router.post(
    "/{file_id}/move",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Move file",
    description="Move a file to a new parent folder or Root storage level.",
)
def move_file(
    file_id: uuid.UUID,
    move_in: FileMove,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Move file to target folder."""
    ip_address = request.client.host if request.client else None
    return FileService.move_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        destination_folder_id=move_in.destination_folder_id,
        ip_address=ip_address,
    )


@router.post(
    "/{file_id}/copy",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Copy / duplicate file",
    description="Duplicate a file into a destination folder, cloning storage binary and updating quota.",
)
def copy_file(
    file_id: uuid.UUID,
    copy_in: FileCopy,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Copy file to destination."""
    ip_address = request.client.host if request.client else None
    return FileService.copy_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        destination_folder_id=copy_in.destination_folder_id,
        new_name=copy_in.new_name,
        ip_address=ip_address,
    )


@router.post(
    "/{file_id}/star",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Toggle file star status",
    description="Add or remove file from user favorites/starred list.",
)
def toggle_star_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Toggle star for a file."""
    is_starred = FileService.toggle_star(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )
    return {
        "file_id": file_id,
        "is_starred": is_starred,
        "message": "File starred." if is_starred else "File unstarred.",
    }


@router.delete(
    "/{file_id}",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete file",
    description="Move a file to the Trash bin.",
)
def soft_delete_file(
    file_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Soft delete file to trash."""
    ip_address = request.client.host if request.client else None
    file = FileService.soft_delete_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    return FileResponse(
        id=file.id,
        name=file.name,
        folder_id=file.folder_id,
        owner_id=file.owner_id,
        mime_type=file.mime_type,
        size_bytes=file.size_bytes,
        storage_path=file.storage_path,
        is_deleted=file.is_deleted,
        deleted_at=file.deleted_at,
        created_at=file.created_at,
        updated_at=file.updated_at,
        is_starred=False,
        current_version_number=FileService.get_current_version_number(db, file.id),
    )


@router.post(
    "/{file_id}/restore",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore file from trash",
    description="Restore a soft-deleted file from the Trash bin back to active status.",
)
def restore_file(
    file_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Restore file from trash."""
    ip_address = request.client.host if request.client else None
    file = FileService.restore_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    is_starred = FileService.is_file_starred(db=db, file_id=file.id, user_id=current_user.id)
    return FileResponse(
        id=file.id,
        name=file.name,
        folder_id=file.folder_id,
        owner_id=file.owner_id,
        mime_type=file.mime_type,
        size_bytes=file.size_bytes,
        storage_path=file.storage_path,
        is_deleted=file.is_deleted,
        deleted_at=file.deleted_at,
        created_at=file.created_at,
        updated_at=file.updated_at,
        is_starred=is_starred,
        current_version_number=FileService.get_current_version_number(db, file.id),
    )


@router.delete(
    "/{file_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete file",
    description="Hard delete file, version history, and storage objects permanently from database and object store.",
)
def permanent_delete_file(
    file_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Permanently delete file."""
    ip_address = request.client.host if request.client else None
    FileService.hard_delete_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )


# ============================================================================
# File Content Previews & Text Inspection
# ============================================================================


@router.get(
    "/{file_id}/preview",
    summary="Stream file preview",
    description="Stream file inline with HTTP 206 Range support for audio/video playback and browser rendering.",
)
def preview_file(
    file_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Inline file preview streaming endpoint supporting byte-range media seeking."""
    range_header = request.headers.get("Range")
    return PreviewService.get_file_preview_response(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        range_header=range_header,
    )


@router.get(
    "/{file_id}/text-content",
    response_model=TextContentResponse,
    summary="Get text file content",
    description="Retrieve raw text or code content for in-browser file viewing or code editor inspection.",
)
def get_text_content(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TextContentResponse:
    """Read and decode text file content with line counts and encoding detection."""
    return PreviewService.get_text_content(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )
