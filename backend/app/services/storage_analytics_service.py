"""Storage analytics service computing metrics, breakdown by category, and quota enforcement."""

from collections import defaultdict
from typing import Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.folder import Folder
from app.models.user import User
from app.schemas.storage_analytics import (
    StorageCategoryBreakdown,
    StorageFileItem,
    StorageUsageSummaryResponse,
)
from app.services.search_service import SearchService


class StorageAnalyticsService:
    """Service providing storage quota verification, analytics, and usage breakdowns."""

    @staticmethod
    def validate_quota_available(db: Session, user_id: uuid.UUID, incoming_bytes: int) -> None:
        """Validate if adding incoming_bytes exceeds the user's storage quota."""
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        quota = settings.DEFAULT_STORAGE_QUOTA_BYTES
        current_used = user.storage_used_bytes or 0
        projected = current_used + incoming_bytes

        if projected > quota:
            available = max(0, quota - current_used)
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=f"Storage quota exceeded. Available space: {available} bytes, Requested: {incoming_bytes} bytes (Quota: {quota} bytes).",
            )

    @staticmethod
    def recalculate_user_storage(db: Session, user_id: uuid.UUID) -> int:
        """Recalculate and update the exact storage consumed by all non-deleted files for a user."""
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            return 0

        # Sum of size_bytes for all non-deleted files owned by user
        total_used = db.scalar(
            select(func.coalesce(func.sum(File.size_bytes), 0)).where(
                File.owner_id == user_id,
                File.is_deleted.is_(False),
            )
        ) or 0

        user.storage_used_bytes = total_used
        db.commit()
        db.refresh(user)
        return total_used

    @classmethod
    def get_storage_summary(cls, db: Session, user_id: uuid.UUID) -> StorageUsageSummaryResponse:
        """Generate comprehensive storage usage metrics and categorical breakdown for a user."""
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        quota = settings.DEFAULT_STORAGE_QUOTA_BYTES
        used = user.storage_used_bytes or 0
        available = max(0, quota - used)
        usage_pct = round((used / quota) * 100, 2) if quota > 0 else 0.0

        # Query all non-deleted files owned by user
        files = db.scalars(
            select(File).where(File.owner_id == user_id, File.is_deleted.is_(False))
        ).all()

        total_files = len(files)
        total_folders = db.scalar(
            select(func.count(Folder.id)).where(
                Folder.owner_id == user_id,
                Folder.is_deleted.is_(False),
            )
        ) or 0

        total_versions = db.scalar(
            select(func.count(FileVersion.id))
            .join(File, File.id == FileVersion.file_id)
            .where(File.owner_id == user_id)
        ) or 0

        trash_bytes = db.scalar(
            select(func.coalesce(func.sum(File.size_bytes), 0)).where(
                File.owner_id == user_id,
                File.is_deleted.is_(True),
            )
        ) or 0

        # Group by category
        category_bytes: Dict[str, int] = defaultdict(int)
        category_counts: Dict[str, int] = defaultdict(int)

        for file in files:
            cat = SearchService.categorize_file(file.name, file.mime_type)
            # Group pdf under documents for storage display
            if cat == "pdf":
                cat = "documents"
            elif cat == "image":
                cat = "images"
            elif cat == "video":
                cat = "videos"
            elif cat == "audio":
                cat = "audio"
            elif cat == "document":
                cat = "documents"
            elif cat == "archive":
                cat = "archives"
            elif cat == "code":
                cat = "code"
            else:
                cat = "other"

            category_bytes[cat] += file.size_bytes or 0
            category_counts[cat] += 1

        all_categories = ["images", "documents", "videos", "audio", "archives", "code", "other"]
        breakdown_list: List[StorageCategoryBreakdown] = []

        for cat in all_categories:
            c_bytes = category_bytes.get(cat, 0)
            c_count = category_counts.get(cat, 0)
            c_pct = round((c_bytes / used) * 100, 2) if used > 0 else 0.0
            breakdown_list.append(
                StorageCategoryBreakdown(
                    category=cat,
                    bytes_used=c_bytes,
                    file_count=c_count,
                    percentage_of_used=c_pct,
                )
            )

        # Largest files (Top 5)
        largest_files_query = (
            select(File)
            .where(File.owner_id == user_id, File.is_deleted.is_(False))
            .order_by(File.size_bytes.desc())
            .limit(5)
        )
        largest_files = [
            StorageFileItem(
                id=f.id,
                name=f.name,
                size_bytes=f.size_bytes,
                mime_type=f.mime_type,
                folder_id=f.folder_id,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in db.scalars(largest_files_query).all()
        ]

        # Recent uploads (Top 5)
        recent_uploads_query = (
            select(File)
            .where(File.owner_id == user_id, File.is_deleted.is_(False))
            .order_by(File.created_at.desc())
            .limit(5)
        )
        recent_uploads = [
            StorageFileItem(
                id=f.id,
                name=f.name,
                size_bytes=f.size_bytes,
                mime_type=f.mime_type,
                folder_id=f.folder_id,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in db.scalars(recent_uploads_query).all()
        ]

        return StorageUsageSummaryResponse(
            storage_used_bytes=used,
            storage_quota_bytes=quota,
            storage_available_bytes=available,
            usage_percentage=usage_pct,
            total_files=total_files,
            total_folders=total_folders,
            total_versions=total_versions,
            trash_bytes=trash_bytes,
            breakdown=breakdown_list,
            largest_files=largest_files,
            recent_uploads=recent_uploads,
        )
