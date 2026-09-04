from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.file import File
from app.models.folder import Folder
from app.models.star import Star
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse
from app.schemas.star import StarredListResponse, StarToggleResponse
from app.services.activity_service import ActivityService
from app.services.share_service import ShareService

class StarService:
    """Business logic for starring/unstarring files and folders and retrieving favorites."""

    @staticmethod
    def toggle_star(
        db: Session,
        user_id: uuid.UUID,
        file_id: Optional[uuid.UUID] = None,
        folder_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> StarToggleResponse:
        """Toggle star/favorite status for a file or folder."""
        if file_id:
            file = db.scalar(select(File).where(File.id == file_id, File.is_deleted.is_(False)))
            if not file:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

            has_access, _ = ShareService.check_user_access(db=db, user_id=user_id, file_id=file_id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this file.")

            existing_star = db.scalar(
                select(Star).where(Star.user_id == user_id, Star.file_id == file_id)
            )

            if existing_star:
                db.delete(existing_star)
                db.commit()
                ActivityService.log_activity(
                    db=db,
                    user_id=user_id,
                    action="ITEM_UNSTARRED",
                    resource_type="FILE",
                    resource_id=file_id,
                    details={"name": file.name},
                    ip_address=ip_address,
                )
                db.commit()
                return StarToggleResponse(
                    is_starred=False,
                    resource_type="file",
                    resource_id=file_id,
                    message="File removed from starred favorites.",
                )
            else:
                new_star = Star(user_id=user_id, file_id=file_id)
                db.add(new_star)
                db.commit()
                ActivityService.log_activity(
                    db=db,
                    user_id=user_id,
                    action="ITEM_STARRED",
                    resource_type="FILE",
                    resource_id=file_id,
                    details={"name": file.name},
                    ip_address=ip_address,
                )
                db.commit()
                return StarToggleResponse(
                    is_starred=True,
                    resource_type="file",
                    resource_id=file_id,
                    message="File added to starred favorites.",
                )

        elif folder_id:
            folder = db.scalar(select(Folder).where(Folder.id == folder_id, Folder.is_deleted.is_(False)))
            if not folder:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

            has_access, _ = ShareService.check_user_access(db=db, user_id=user_id, folder_id=folder_id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this folder.")

            existing_star = db.scalar(
                select(Star).where(Star.user_id == user_id, Star.folder_id == folder_id)
            )

            if existing_star:
                db.delete(existing_star)
                db.commit()
                ActivityService.log_activity(
                    db=db,
                    user_id=user_id,
                    action="ITEM_UNSTARRED",
                    resource_type="FOLDER",
                    resource_id=folder_id,
                    details={"name": folder.name},
                    ip_address=ip_address,
                )
                db.commit()
                return StarToggleResponse(
                    is_starred=False,
                    resource_type="folder",
                    resource_id=folder_id,
                    message="Folder removed from starred favorites.",
                )
            else:
                new_star = Star(user_id=user_id, folder_id=folder_id)
                db.add(new_star)
                db.commit()
                ActivityService.log_activity(
                    db=db,
                    user_id=user_id,
                    action="ITEM_STARRED",
                    resource_type="FOLDER",
                    resource_id=folder_id,
                    details={"name": folder.name},
                    ip_address=ip_address,
                )
                db.commit()
                return StarToggleResponse(
                    is_starred=True,
                    resource_type="folder",
                    resource_id=folder_id,
                    message="Folder added to starred favorites.",
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify either file_id or folder_id to toggle star.",
            )

    @staticmethod
    def list_starred(db: Session, user_id: uuid.UUID) -> StarredListResponse:
        """Retrieve unified list of all active starred files and folders."""
        stars = db.scalars(
            select(Star)
            .options(joinedload(Star.file), joinedload(Star.folder))
            .where(Star.user_id == user_id)
            .order_by(Star.created_at.desc())
        ).all()

        from app.services.file_service import FileService

        starred_files: List[FileResponse] = []
        starred_folders: List[FolderResponse] = []

        for star in stars:
            if star.file and not star.file.is_deleted:
                ver_num = FileService.get_current_version_number(db, star.file.id)
                starred_files.append(
                    FileResponse(
                        id=star.file.id,
                        name=star.file.name,
                        folder_id=star.file.folder_id,
                        owner_id=star.file.owner_id,
                        mime_type=star.file.mime_type,
                        size_bytes=star.file.size_bytes,
                        storage_path=star.file.storage_path,
                        is_deleted=star.file.is_deleted,
                        deleted_at=star.file.deleted_at,
                        created_at=star.file.created_at,
                        updated_at=star.file.updated_at,
                        is_starred=True,
                        current_version_number=ver_num,
                    )
                )
            elif star.folder and not star.folder.is_deleted:
                starred_folders.append(
                    FolderResponse(
                        id=star.folder.id,
                        name=star.folder.name,
                        parent_id=star.folder.parent_id,
                        owner_id=star.folder.owner_id,
                        color=star.folder.color,
                        is_deleted=star.folder.is_deleted,
                        deleted_at=star.folder.deleted_at,
                        created_at=star.folder.created_at,
                        updated_at=star.folder.updated_at,
                        is_starred=True,
                    )
                )

        return StarredListResponse(
            folders=starred_folders,
            files=starred_files,
            total_count=len(starred_folders) + len(starred_files),
        )
