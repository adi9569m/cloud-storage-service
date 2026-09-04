from typing import List, Optional
import uuid
from pydantic import BaseModel, Field

class BatchItemSelection(BaseModel):
    """Selection of file and folder IDs for batch processing."""

    file_ids: List[uuid.UUID] = Field(default_factory=list, description="List of file UUIDs to process")
    folder_ids: List[uuid.UUID] = Field(default_factory=list, description="List of folder UUIDs to process")

class BatchMoveRequest(BatchItemSelection):
    """Request payload to move multiple files and folders to a destination folder."""

    destination_folder_id: Optional[uuid.UUID] = Field(
        None, description="Target destination folder UUID (None for root directory)"
    )

class BatchCopyRequest(BaseModel):
    """Request payload to copy multiple files to a destination folder."""

    file_ids: List[uuid.UUID] = Field(default_factory=list, description="List of file UUIDs to duplicate")
    destination_folder_id: Optional[uuid.UUID] = Field(
        None, description="Target destination folder UUID (None for root directory)"
    )

class BatchStarRequest(BatchItemSelection):
    """Request payload to star or unstar multiple items in bulk."""

    is_starred: bool = Field(True, description="True to star, False to unstar")

class BatchFailureDetail(BaseModel):
    """Details for an item that failed during a batch operation."""

    id: uuid.UUID
    resource_type: str = Field(..., description="'file' or 'folder'")
    reason: str

class BatchOperationResult(BaseModel):
    """Result summary of a completed batch operation."""

    succeeded_files: List[uuid.UUID] = Field(default_factory=list)
    succeeded_folders: List[uuid.UUID] = Field(default_factory=list)
    failed: List[BatchFailureDetail] = Field(default_factory=list)
    total_succeeded: int = 0
    total_failed: int = 0
    message: str = "Batch operation completed"
