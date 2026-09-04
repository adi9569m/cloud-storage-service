from datetime import datetime
import math
import os
from typing import Dict, List, Optional, Set, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.folder import Folder
from app.models.star import Star
from app.schemas.search import (
    SearchFacets,
    SearchResponse,
    SearchResultItem,
    SearchSortBy,
    SearchSortOrder,
    SearchTypeFilter,
)
from app.services.folder_service import FolderService

class SearchService:
    """Service handling multi-faceted file and folder search queries."""

    IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff", "ico", "heic", "avif"}
    VIDEO_EXTS = {"mp4", "mkv", "mov", "avi", "wmv", "flv", "webm", "m4v", "3gp"}
    AUDIO_EXTS = {"mp3", "wav", "ogg", "m4a", "flac", "aac", "wma", "aiff"}
    DOCUMENT_EXTS = {
        "pdf", "doc", "docx", "txt", "rtf", "odt", "xls", "xlsx", "ppt", "pptx", "csv", "tsv", "pages", "numbers", "key"
    }
    PDF_EXTS = {"pdf"}
    ARCHIVE_EXTS = {"zip", "tar", "gz", "tgz", "7z", "rar", "bz2", "xz", "iso"}
    CODE_EXTS = {
        "py", "js", "jsx", "ts", "tsx", "html", "htm", "css", "scss", "sass", "less", "json", "xml", "yaml", "yml",
        "md", "markdown", "sql", "sh", "bash", "zsh", "ps1", "c", "cpp", "h", "hpp", "java", "rs", "go", "php",
        "rb", "swift", "kt", "scala", "env", "dockerfile", "toml", "ini", "conf"
    }

    @classmethod
    def categorize_file(cls, filename: str, mime_type: Optional[str] = None) -> str:
        """Classify file into standard categories based on MIME type and file extension."""
        mime = (mime_type or "").lower()
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if mime.startswith("image/") or ext in cls.IMAGE_EXTS:
            return "image"
        if mime.startswith("video/") or ext in cls.VIDEO_EXTS:
            return "video"
        if mime.startswith("audio/") or ext in cls.AUDIO_EXTS:
            return "audio"
        if mime == "application/pdf" or ext in cls.PDF_EXTS:
            return "pdf"
        if (
            "zip" in mime
            or "compressed" in mime
            or "tar" in mime
            or "archive" in mime
            or ext in cls.ARCHIVE_EXTS
        ):
            return "archive"
        if (
            "json" in mime
            or "javascript" in mime
            or "typescript" in mime
            or "xml" in mime
            or "python" in mime
            or ext in cls.CODE_EXTS
        ):
            return "code"
        if (
            mime.startswith("text/")
            or "word" in mime
            or "sheet" in mime
            or "presentation" in mime
            or "officedocument" in mime
            or ext in cls.DOCUMENT_EXTS
        ):
            return "document"
        return "other"

    @classmethod
    def _build_folder_path_map(cls, db: Session, user_id: uuid.UUID) -> Dict[uuid.UUID, str]:
        """Build dictionary mapping folder ID to absolute breadcrumb path for fast resolution."""
        folders = db.scalars(
            select(Folder).where(Folder.owner_id == user_id, Folder.is_deleted.is_(False))
        ).all()
        folder_dict = {f.id: f for f in folders}
        path_cache: Dict[uuid.UUID, str] = {}

        def get_path(fid: uuid.UUID) -> str:
            if fid in path_cache:
                return path_cache[fid]
            folder = folder_dict.get(fid)
            if not folder:
                return ""
            if folder.parent_id and folder.parent_id in folder_dict:
                parent_path = get_path(folder.parent_id)
                full = f"{parent_path}/{folder.name}" if parent_path else f"/{folder.name}"
            else:
                full = f"/{folder.name}"
            path_cache[fid] = full
            return full

        for fid in folder_dict:
            get_path(fid)

        return path_cache

    @classmethod
    def search(
        cls,
        db: Session,
        user_id: uuid.UUID,
        q: Optional[str] = None,
        type_filter: SearchTypeFilter = SearchTypeFilter.ALL,
        mime_type: Optional[str] = None,
        extension: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        folder_id: Optional[uuid.UUID] = None,
        is_starred: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        sort_by: SearchSortBy = SearchSortBy.UPDATED_AT,
        sort_order: SearchSortOrder = SearchSortOrder.DESC,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """Execute comprehensive search with faceted counts, filtering, and pagination."""
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        starred_file_ids: Set[uuid.UUID] = set(
            db.scalars(
                select(Star.file_id).where(Star.user_id == user_id, Star.file_id.is_not(None))
            ).all()
        )
        starred_folder_ids: Set[uuid.UUID] = set(
            db.scalars(
                select(Star.folder_id).where(Star.user_id == user_id, Star.folder_id.is_not(None))
            ).all()
        )

        allowed_folder_ids: Optional[Set[uuid.UUID]] = None
        if folder_id is not None:

            allowed_folder_ids = {folder_id}
            allowed_folder_ids.update(
                FolderService._get_all_descendant_folder_ids(db, folder_id, user_id)
            )

        folder_paths = cls._build_folder_path_map(db, user_id)

        has_file_specific_filter = bool(
            mime_type or extension or (min_size is not None) or (max_size is not None)
        )

        folder_stmt = select(Folder).where(
            Folder.owner_id == user_id,
            Folder.is_deleted.is_(False),
        )
        file_stmt = select(File).where(
            File.owner_id == user_id,
            File.is_deleted.is_(False),
        )

        if q:
            term = f"%{q.strip()}%"
            folder_stmt = folder_stmt.where(Folder.name.ilike(term))
            file_stmt = file_stmt.where(File.name.ilike(term))

        if folder_id is not None and allowed_folder_ids is not None:
            folder_stmt = folder_stmt.where(
                (Folder.id.in_(allowed_folder_ids)) | (Folder.parent_id.in_(allowed_folder_ids))
            )
            file_stmt = file_stmt.where(File.folder_id.in_(allowed_folder_ids))

        if created_after:
            folder_stmt = folder_stmt.where(Folder.created_at >= created_after)
            file_stmt = file_stmt.where(File.created_at >= created_after)

        if created_before:
            folder_stmt = folder_stmt.where(Folder.created_at <= created_before)
            file_stmt = file_stmt.where(File.created_at <= created_before)

        if updated_after:
            folder_stmt = folder_stmt.where(Folder.updated_at >= updated_after)
            file_stmt = file_stmt.where(File.updated_at >= updated_after)

        if updated_before:
            folder_stmt = folder_stmt.where(Folder.updated_at <= updated_before)
            file_stmt = file_stmt.where(File.updated_at <= updated_before)

        if min_size is not None:
            file_stmt = file_stmt.where(File.size_bytes >= min_size)

        if max_size is not None:
            file_stmt = file_stmt.where(File.size_bytes <= max_size)

        if mime_type:
            file_stmt = file_stmt.where(File.mime_type.ilike(f"%{mime_type.strip()}%"))

        if extension:
            clean_ext = extension.strip().lstrip(".")
            file_stmt = file_stmt.where(File.name.ilike(f"%.{clean_ext}"))

        candidate_folders: List[Folder] = [] if has_file_specific_filter else db.scalars(folder_stmt).all()
        candidate_files: List[File] = db.scalars(file_stmt).all()

        all_items: List[SearchResultItem] = []
        facets = SearchFacets()

        for folder in candidate_folders:
            is_star = folder.id in starred_folder_ids
            if is_starred is not None and is_star != is_starred:
                continue

            path = folder_paths.get(folder.id, f"/{folder.name}")
            item = SearchResultItem(
                id=folder.id,
                name=folder.name,
                resource_type="folder",
                folder_id=folder.parent_id,
                owner_id=folder.owner_id,
                mime_type=None,
                size_bytes=None,
                color=folder.color,
                is_starred=is_star,
                path=path,
                created_at=folder.created_at,
                updated_at=folder.updated_at,
            )
            facets.folders += 1
            facets.all += 1
            if type_filter in (SearchTypeFilter.ALL, SearchTypeFilter.FOLDER):
                all_items.append(item)

        for file in candidate_files:
            is_star = file.id in starred_file_ids
            if is_starred is not None and is_star != is_starred:
                continue

            category = cls.categorize_file(file.name, file.mime_type)
            facets.files += 1
            facets.all += 1

            if category == "image":
                facets.images += 1
            elif category == "video":
                facets.videos += 1
            elif category == "audio":
                facets.audio += 1
            elif category == "pdf":
                facets.documents += 1
                facets.other += 0
            elif category == "document":
                facets.documents += 1
            elif category == "archive":
                facets.archives += 1
            elif category == "code":
                facets.code += 1
            else:
                facets.other += 1

            include = False
            if type_filter == SearchTypeFilter.ALL or type_filter == SearchTypeFilter.FILE:
                include = True
            elif type_filter == SearchTypeFilter.IMAGE and category == "image":
                include = True
            elif type_filter == SearchTypeFilter.VIDEO and category == "video":
                include = True
            elif type_filter == SearchTypeFilter.AUDIO and category == "audio":
                include = True
            elif type_filter == SearchTypeFilter.PDF and (category == "pdf" or file.name.lower().endswith(".pdf")):
                include = True
            elif type_filter == SearchTypeFilter.DOCUMENT and (category in ("document", "pdf")):
                include = True
            elif type_filter == SearchTypeFilter.ARCHIVE and category == "archive":
                include = True
            elif type_filter == SearchTypeFilter.CODE and category == "code":
                include = True
            elif type_filter == SearchTypeFilter.OTHER and category == "other":
                include = True

            if include:
                folder_path = folder_paths.get(file.folder_id, "") if file.folder_id else ""
                full_path = f"{folder_path}/{file.name}" if folder_path else f"/{file.name}"

                item = SearchResultItem(
                    id=file.id,
                    name=file.name,
                    resource_type="file",
                    folder_id=file.folder_id,
                    owner_id=file.owner_id,
                    mime_type=file.mime_type,
                    size_bytes=file.size_bytes,
                    color=None,
                    is_starred=is_star,
                    path=full_path,
                    created_at=file.created_at,
                    updated_at=file.updated_at,
                )
                all_items.append(item)

        reverse = (sort_order == SearchSortOrder.DESC)
        if sort_by == SearchSortBy.NAME:
            all_items.sort(key=lambda x: x.name.lower(), reverse=reverse)
        elif sort_by == SearchSortBy.CREATED_AT:
            all_items.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == SearchSortBy.SIZE_BYTES:
            all_items.sort(key=lambda x: x.size_bytes or 0, reverse=reverse)
        else:
            all_items.sort(key=lambda x: x.updated_at, reverse=reverse)

        total = len(all_items)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        paginated_items = all_items[start_idx : start_idx + page_size]

        return SearchResponse(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            facets=facets,
            query=q,
        )
