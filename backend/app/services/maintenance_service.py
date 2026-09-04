from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.folder import Folder
from app.models.link_share import LinkShare
from app.models.user import User
from app.schemas.maintenance import (
    ExpiredLinksCleanupResult,
    MaintenanceCleanupResult,
    StorageSyncResult,
    SystemStatusResponse,
)
from app.services.file_service import FileService
from app.services.folder_service import FolderService
from app.services.storage_analytics_service import StorageAnalyticsService

class MaintenanceService:
    """Service executing maintenance background tasks, data retention, and telemetry."""

    @classmethod
    def cleanup_old_trash(
        cls,
        db: Session,
        older_than_days: int = 30,
        dry_run: bool = False,
    ) -> MaintenanceCleanupResult:
        """Purge soft-deleted files and folders that have exceeded the retention threshold."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        old_files = db.scalars(
            select(File).where(File.is_deleted.is_(True), File.deleted_at <= cutoff_date)
        ).all()

        old_folders = db.scalars(
            select(Folder).where(Folder.is_deleted.is_(True), Folder.deleted_at <= cutoff_date)
        ).all()

        freed_bytes = sum(f.size_bytes or 0 for f in old_files)

        if not dry_run:
            affected_users = set()

            for folder in old_folders:
                affected_users.add(folder.owner_id)
                FolderService.hard_delete_folder(db=db, folder_id=folder.id, user_id=folder.owner_id)

            for file in old_files:
                affected_users.add(file.owner_id)
                FileService.hard_delete_file(db=db, file_id=file.id, user_id=file.owner_id)

            for uid in affected_users:
                StorageAnalyticsService.recalculate_user_storage(db, uid)

        return MaintenanceCleanupResult(
            purged_files_count=len(old_files),
            purged_folders_count=len(old_folders),
            freed_bytes=freed_bytes,
            dry_run=dry_run,
            message=(
                f"Dry run: {len(old_files)} files and {len(old_folders)} folders ({freed_bytes} bytes) would be purged."
                if dry_run
                else f"Cleaned up {len(old_files)} files and {len(old_folders)} folders. Reclaimed {freed_bytes} bytes."
            ),
        )

    @classmethod
    def cleanup_expired_links(cls, db: Session) -> ExpiredLinksCleanupResult:
        """Deactivate all public link shares that have passed their expiration timestamp."""
        now = datetime.now(timezone.utc)
        expired_links = db.scalars(
            select(LinkShare).where(
                LinkShare.is_active.is_(True),
                LinkShare.expires_at.is_not(None),
                LinkShare.expires_at <= now,
            )
        ).all()

        for link in expired_links:
            link.is_active = False

        db.commit()

        return ExpiredLinksCleanupResult(
            deactivated_links_count=len(expired_links),
            message=f"Deactivated {len(expired_links)} expired public share links.",
        )

    @classmethod
    def sync_storage_quotas(cls, db: Session) -> StorageSyncResult:
        """Re-synchronize storage consumption across all registered users."""
        users = db.scalars(select(User)).all()
        total_storage = 0

        for user in users:
            used = StorageAnalyticsService.recalculate_user_storage(db, user.id)
            total_storage += used

        return StorageSyncResult(
            users_synced=len(users),
            total_storage_bytes=total_storage,
            message=f"Successfully synchronized storage quotas for {len(users)} users.",
        )

    @classmethod
    def get_system_status(cls, db: Session) -> SystemStatusResponse:
        """Retrieve system-level health status and aggregated telemetry."""
        total_users = db.scalar(select(func.count(User.id))) or 0
        total_files = db.scalar(select(func.count(File.id)).where(File.is_deleted.is_(False))) or 0
        total_folders = db.scalar(select(func.count(Folder.id)).where(Folder.is_deleted.is_(False))) or 0
        total_storage_bytes = db.scalar(
            select(func.coalesce(func.sum(File.size_bytes), 0)).where(File.is_deleted.is_(False))
        ) or 0

        return SystemStatusResponse(
            status="healthy",
            environment=settings.APP_ENV,
            total_users=total_users,
            total_files=total_files,
            total_folders=total_folders,
            total_storage_bytes=total_storage_bytes,
            rate_limiting_enabled=settings.RATE_LIMIT_ENABLED,
            timestamp=datetime.now(timezone.utc),
        )
