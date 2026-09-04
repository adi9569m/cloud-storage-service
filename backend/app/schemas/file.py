import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import BreadcrumbItem

class FileBase(BaseModel):
    """Base schema for file attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="File name including extension.")
    mime_type: str = Field(..., max_length=127, description="MIME type format.")

class FileUploadInit(BaseModel):
    """Payload to initiate a direct or presigned file upload."""

    name: str = Field(..., min_length=1, max_length=255, description="File name including extension.")
    mime_type: str = Field(..., max_length=127, description="MIME type format (e.g. application/pdf).")
    size_bytes: int = Field(..., ge=0, description="Expected file size in bytes.")
    folder_id: Optional[uuid.UUID] = Field(None, description="Parent folder ID. Null represents Root.")

class FileUploadInitResponse(BaseModel):
    """Response returned upon upload initialization with presigned upload URL."""

    file_id: uuid.UUID
    version_number: int
    storage_path: str
    upload_url: str
    expires_in_seconds: int
    method: str = "PUT"

class FileUploadComplete(BaseModel):
    """Payload to confirm upload completion and finalize metadata."""

    file_id: uuid.UUID
    version_number: int = 1
    checksum_sha256: Optional[str] = Field(None, max_length=64, description="SHA-256 integrity hash.")
    actual_size_bytes: Optional[int] = Field(None, ge=0, description="Confirmed size in bytes if different from init.")

class FileVersionInit(BaseModel):
    """Payload to initiate a new version upload for an existing file."""

    size_bytes: int = Field(..., ge=0, description="Size in bytes of the new version.")
    mime_type: Optional[str] = Field(None, max_length=127, description="Optional new MIME type.")

class FileVersionInitResponse(BaseModel):
    """Response returned upon version upload initialization."""

    file_id: uuid.UUID
    version_number: int
    storage_path: str
    upload_url: str
    expires_in_seconds: int
    method: str = "PUT"

class FileVersionComplete(BaseModel):
    """Payload to confirm new version upload completion."""

    version_number: int
    checksum_sha256: Optional[str] = Field(None, max_length=64, description="SHA-256 integrity hash.")
    actual_size_bytes: Optional[int] = Field(None, ge=0, description="Confirmed size in bytes.")

class FileVersionResponse(BaseModel):
    """Schema representing an immutable file version record."""

    id: uuid.UUID
    file_id: uuid.UUID
    version_number: int
    storage_path: str
    size_bytes: int
    mime_type: str
    checksum_sha256: Optional[str] = None
    uploaded_by_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileUpdate(BaseModel):
    """Schema for updating file metadata (renaming)."""

    name: str = Field(..., min_length=1, max_length=255, description="New file name with extension.")

class FileMove(BaseModel):
    """Schema for relocating a file to a new parent folder."""

    destination_folder_id: Optional[uuid.UUID] = Field(None, description="Target destination folder ID. Null for Root.")

class FileCopy(BaseModel):
    """Schema for copying/duplicating a file."""

    destination_folder_id: Optional[uuid.UUID] = Field(None, description="Target destination folder ID. Null for Root.")
    new_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Optional new name for the duplicate.")

class FileDownloadResponse(BaseModel):
    """Response containing signed download URL and file metadata."""

    download_url: str
    file_id: uuid.UUID
    name: str
    mime_type: str
    size_bytes: int
    version_number: int
    expires_in_seconds: int

class FileResponse(BaseModel):
    """File metadata response schema."""

    id: uuid.UUID
    name: str
    folder_id: Optional[uuid.UUID]
    owner_id: uuid.UUID
    mime_type: str
    size_bytes: int
    storage_path: str
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_starred: bool = False
    current_version_number: int = 1

    model_config = ConfigDict(from_attributes=True)

class FileDetailResponse(FileResponse):
    """Detailed file response including breadcrumbs and full version history."""

    breadcrumbs: List[BreadcrumbItem] = Field(default_factory=list)
    versions: List[FileVersionResponse] = Field(default_factory=list)
    versions_count: int = 1

class FileListResponse(BaseModel):
    """List response for files search and collections."""

    items: List[FileResponse]
    total_count: int

class ArchiveExtractRequest(BaseModel):
    destination_folder_id: Optional[uuid.UUID] = Field(
        None, description="Target folder to extract contents into. If omitted, uses parent folder of archive."
    )
    create_subfolder: bool = Field(
        True, description="Whether to extract contents into a new container folder named after the archive."
    )

class ArchiveExtractResponse(BaseModel):
    destination_folder_id: Optional[uuid.UUID]
    extracted_folder_name: Optional[str]
    files_count: int
    folders_count: int
    total_unpacked_bytes: int

class ChecksumVerificationResponse(BaseModel):
    file_id: uuid.UUID
    version_number: int
    expected_checksum: Optional[str]
    actual_checksum: str
    is_valid: bool
    checked_at: datetime
