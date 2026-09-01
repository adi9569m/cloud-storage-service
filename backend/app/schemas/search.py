"""Pydantic schemas for multi-facet search and filtering."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class SearchTypeFilter(str, Enum):
    """Filter resource types or file categories."""

    ALL = "all"
    FILE = "file"
    FOLDER = "folder"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    PDF = "pdf"
    ARCHIVE = "archive"
    CODE = "code"
    OTHER = "other"


class SearchSortBy(str, Enum):
    """Sortable fields for search results."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    SIZE_BYTES = "size_bytes"


class SearchSortOrder(str, Enum):
    """Sorting direction."""

    ASC = "asc"
    DESC = "desc"


class SearchResultItem(BaseModel):
    """Single item returned in search results representing a file or folder."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    resource_type: str = Field(..., description="'file' or 'folder'")
    folder_id: Optional[uuid.UUID] = None
    owner_id: uuid.UUID
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    color: Optional[str] = None
    is_starred: bool = False
    path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SearchFacets(BaseModel):
    """Facet count breakdown for search queries."""

    all: int = 0
    files: int = 0
    folders: int = 0
    images: int = 0
    documents: int = 0
    videos: int = 0
    audio: int = 0
    archives: int = 0
    code: int = 0
    other: int = 0


class SearchResponse(BaseModel):
    """Paginated search response with faceted count breakdown."""

    items: List[SearchResultItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    facets: SearchFacets
    query: Optional[str] = None
