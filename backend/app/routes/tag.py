"""API router for custom color tags, item labeling, and tagged collections."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.tag import (
    TagAttachRequest,
    TagCreate,
    TagDetachRequest,
    TaggedItemsResponse,
    TagResponse,
    TagUpdate,
)
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["Tags & Labels"])


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_in: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TagResponse:
    """Create a new custom color label tag."""
    return TagService.create_tag(db=db, user_id=current_user.id, tag_in=tag_in)


@router.get("", response_model=List[TagResponse])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TagResponse]:
    """List all custom tags created by the current user."""
    return TagService.list_user_tags(db=db, user_id=current_user.id)


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TagResponse:
    """Update tag name or color."""
    return TagService.update_tag(db=db, tag_id=tag_id, user_id=current_user.id, tag_in=tag_in)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete tag and clear all its item associations."""
    TagService.delete_tag(db=db, tag_id=tag_id, user_id=current_user.id)


@router.post("/attach", status_code=status.HTTP_200_OK)
def attach_tag(
    payload: TagAttachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Attach a tag to a target file or folder."""
    TagService.attach_tag(db=db, user_id=current_user.id, attach_in=payload)
    return {"message": "Tag attached successfully."}


@router.post("/detach", status_code=status.HTTP_200_OK)
def detach_tag(
    payload: TagDetachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Detach a tag from a target file or folder."""
    TagService.detach_tag(db=db, user_id=current_user.id, detach_in=payload)
    return {"message": "Tag detached successfully."}


@router.get("/{tag_id}/items", response_model=TaggedItemsResponse)
def get_tagged_items(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaggedItemsResponse:
    """Retrieve all files and folders attached to a specific tag."""
    return TagService.get_tagged_items(db=db, tag_id=tag_id, user_id=current_user.id)


@router.get("/items/file/{file_id}", response_model=List[TagResponse])
def get_file_tags(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TagResponse]:
    """Retrieve all tags attached to a specific file."""
    return TagService.list_tags_for_item(db=db, user_id=current_user.id, file_id=file_id)


@router.get("/items/folder/{folder_id}", response_model=List[TagResponse])
def get_folder_tags(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TagResponse]:
    """Retrieve all tags attached to a specific folder."""
    return TagService.list_tags_for_item(db=db, user_id=current_user.id, folder_id=folder_id)
