"""API router for multi-faceted search and advanced filtering."""

from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.search import (
    SearchResponse,
    SearchSortBy,
    SearchSortOrder,
    SearchTypeFilter,
)
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
def search_items(
    q: Optional[str] = Query(None, description="Search keyword matching file or folder names"),
    type: SearchTypeFilter = Query(SearchTypeFilter.ALL, description="Resource type or file category filter"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type substring"),
    extension: Optional[str] = Query(None, description="Filter by file extension (e.g. pdf, png, docx)"),
    min_size: Optional[int] = Query(None, ge=0, description="Minimum file size in bytes"),
    max_size: Optional[int] = Query(None, ge=0, description="Maximum file size in bytes"),
    folder_id: Optional[uuid.UUID] = Query(None, description="Scope search to this folder and its subfolders"),
    is_starred: Optional[bool] = Query(None, description="Filter for starred items only"),
    created_after: Optional[datetime] = Query(None, description="Filter items created on or after ISO timestamp"),
    created_before: Optional[datetime] = Query(None, description="Filter items created on or before ISO timestamp"),
    updated_after: Optional[datetime] = Query(None, description="Filter items updated on or after ISO timestamp"),
    updated_before: Optional[datetime] = Query(None, description="Filter items updated on or before ISO timestamp"),
    sort_by: SearchSortBy = Query(SearchSortBy.UPDATED_AT, description="Field to sort by"),
    sort_order: SearchSortOrder = Query(SearchSortOrder.DESC, description="Sort direction (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SearchResponse:
    """Search user's files and folders with multi-faceted filtering, sorting, pagination, and category facets."""
    return SearchService.search(
        db=db,
        user_id=current_user.id,
        q=q,
        type_filter=type,
        mime_type=mime_type,
        extension=extension,
        min_size=min_size,
        max_size=max_size,
        folder_id=folder_id,
        is_starred=is_starred,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
