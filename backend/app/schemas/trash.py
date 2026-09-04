from typing import List
from pydantic import BaseModel, Field
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse

class TrashListResponse(BaseModel):
    """Unified listing response containing all soft-deleted folders and files."""

    folders: List[FolderResponse] = Field(default_factory=list)
    files: List[FileResponse] = Field(default_factory=list)
    total_count: int = 0

class TrashRestoreAllResponse(BaseModel):
    """Response returned upon restoring all items from trash."""

    restored_folders_count: int = 0
    restored_files_count: int = 0
    message: str = "All items restored successfully."

class TrashEmptyResponse(BaseModel):
    """Response returned upon permanently emptying the trash bin."""

    deleted_folders_count: int = 0
    deleted_files_count: int = 0
    purged_bytes: int = 0
    message: str = "Trash emptied and storage purged successfully."
