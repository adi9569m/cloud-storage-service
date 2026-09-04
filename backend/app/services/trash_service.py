from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.folder import Folder
from app.models.user import User
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse
from app.schemas.trash import (
    TrashEmptyResponse,
    TrashListResponse,
    TrashRestoreAllResponse,
)
from app.services.activity_service import ActivityService
from app.services.storage_service import StorageService

class TrashService:
    """Business logic for trash inspection, restoration, and permanent storage purge."""

    @staticmethod
    def list_trash(db: Session, user_id: uuid.UUID) -> TrashListResponse:
        """Retrieve all soft-deleted folders and files owned by the user."""
        folders = db.scalars(
            select(Folder)
            .where(Folder.owner_id == user_id, Folder.is_deleted.is_(True))
            .order_by(Folder.deleted_at.desc())
        ).all()

        files = db.scalars(
            select(File)
            .where(File.owner_id == user_id, File.is_deleted.is_(True))
            .order_by(File.deleted_at.desc())
        ).all()

        from app.services.file_service import FileService

        folder_responses = [
            FolderResponse(
                id=f.id,
                name=f.name,
                parent_id=f.parent_id,
                owner_id=f.owner_id,
                color=f.color,
                is_deleted=f.is_deleted,
                deleted_at=f.deleted_at,
                created_at=f.created_at,
                updated_at=f.updated_at,
                is_starred=False,
            )
            for f in folders
        ]

        file_responses = [
            FileResponse(
                id=fi.id,
                name=fi.name,
                folder_id=fi.folder_id,
                owner_id=fi.owner_id,
                mime_type=fi.mime_type,
                size_bytes=fi.size_bytes,
                storage_path=fi.storage_path,
                is_deleted=fi.is_deleted,
                deleted_at=fi.deleted_at,
                created_at=fi.created_at,
                updated_at=fi.updated_at,
                is_starred=False,
                current_version_number=FileService.get_current_version_number(db, fi.id),
            )
            for fi in files
        ]

        return TrashListResponse(
            folders=folder_responses,
            files=file_responses,
            total_count=len(folder_responses) + len(file_responses),
        )

    @staticmethod
    def restore_all(
        db: Session,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TrashRestoreAllResponse:
        """Restore all soft-deleted files and folders belonging to the user."""
        folders = db.scalars(
            select(Folder).where(Folder.owner_id == user_id, Folder.is_deleted.is_(True))
        ).all()

        files = db.scalars(
            select(File).where(File.owner_id == user_id, File.is_deleted.is_(True))
        ).all()

        restored_folders_count = len(folders)
        restored_files_count = len(files)

        for folder in folders:
            folder.is_deleted = False
            folder.deleted_at = None
            if folder.parent_id:

                parent = db.scalar(
                    select(Folder).where(
                        Folder.id == folder.parent_id,
                        Folder.owner_id == user_id,
                    )
                )
                if not parent or parent.is_deleted:
                    folder.parent_id = None

        for file in files:
            file.is_deleted = False
            file.deleted_at = None
            if file.folder_id:
                folder = db.scalar(
                    select(Folder).where(
                        Folder.id == file.folder_id,
                        Folder.owner_id == user_id,
                    )
                )
                if not folder or folder.is_deleted:
                    file.folder_id = None

        db.commit()

        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="TRASH_RESTORE_ALL",
            resource_type="USER",
            resource_id=user_id,
            details={
                "restored_folders_count": restored_folders_count,
                "restored_files_count": restored_files_count,
            },
            ip_address=ip_address,
        )
        db.commit()

        return TrashRestoreAllResponse(
            restored_folders_count=restored_folders_count,
            restored_files_count=restored_files_count,
            message="All items in trash have been successfully restored.",
        )

    @staticmethod
    def empty_trash(
        db: Session,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TrashEmptyResponse:
        """Permanently delete all trash items and purge binary blobs from object storage."""
        files = db.scalars(
            select(File).where(File.owner_id == user_id, File.is_deleted.is_(True))
        ).all()

        purged_bytes = 0
        deleted_files_count = len(files)

        for file in files:
            purged_bytes += file.size_bytes

            versions = db.scalars(
                select(FileVersion).where(FileVersion.file_id == file.id)
            ).all()
            for v in versions:
                try:
                    StorageService.delete_file(v.storage_path)
                except Exception:
                    pass

            db.delete(file)

        folders = db.scalars(
            select(Folder).where(Folder.owner_id == user_id, Folder.is_deleted.is_(True))
        ).all()
        deleted_folders_count = len(folders)

        for folder in folders:
            db.delete(folder)

        user = db.scalar(select(User).where(User.id == user_id))
        if user:
            user.storage_used_bytes = max(0, user.storage_used_bytes - purged_bytes)

        db.commit()

        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="TRASH_EMPTIED",
            resource_type="USER",
            resource_id=user_id,
            details={
                "deleted_folders_count": deleted_folders_count,
                "deleted_files_count": deleted_files_count,
                "purged_bytes": purged_bytes,
            },
            ip_address=ip_address,
        )
        db.commit()

        return TrashEmptyResponse(
            deleted_folders_count=deleted_folders_count,
            deleted_files_count=deleted_files_count,
            purged_bytes=purged_bytes,
            message="Trash emptied and storage permanently purged.",
        )
