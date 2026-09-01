"""Batch service executing bulk operations on mixed file and folder selections."""

import io
from typing import Dict, List, Optional, Set
import uuid
import zipfile
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.folder import Folder
from app.models.star import Star
from app.schemas.batch import (
    BatchFailureDetail,
    BatchOperationResult,
)
from app.schemas.file import FileCopy, FileMove
from app.schemas.folder import FolderMove
from app.services.activity_service import ActivityService
from app.services.file_service import FileService
from app.services.folder_service import FolderService
from app.services.storage_service import StorageService


class BatchService:
    """Service handling bulk operations across multiple files and folders."""

    @classmethod
    def validate_batch_size(cls, file_ids: List[uuid.UUID], folder_ids: List[uuid.UUID]) -> None:
        """Ensure total requested items do not exceed the configured maximum batch size."""
        total = len(file_ids) + len(folder_ids)
        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch request must contain at least one file or folder ID.",
            )
        if total > settings.MAX_BATCH_OPERATION_ITEMS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch operation exceeds maximum allowed items ({settings.MAX_BATCH_OPERATION_ITEMS}).",
            )

    @classmethod
    def batch_delete(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        folder_ids: List[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> BatchOperationResult:
        """Bulk soft-delete files and folders."""
        cls.validate_batch_size(file_ids, folder_ids)
        succeeded_files: List[uuid.UUID] = []
        succeeded_folders: List[uuid.UUID] = []
        failed: List[BatchFailureDetail] = []

        # Process folders first
        for fid in folder_ids:
            try:
                FolderService.soft_delete_folder(db=db, folder_id=fid, user_id=user_id, ip_address=ip_address)
                succeeded_folders.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="folder", reason=str(detail)))

        # Process files
        for fid in file_ids:
            try:
                FileService.soft_delete_file(db=db, file_id=fid, user_id=user_id, ip_address=ip_address)
                succeeded_files.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="file", reason=str(detail)))

        return BatchOperationResult(
            succeeded_files=succeeded_files,
            succeeded_folders=succeeded_folders,
            failed=failed,
            total_succeeded=len(succeeded_files) + len(succeeded_folders),
            total_failed=len(failed),
            message=f"Batch delete: {len(succeeded_files) + len(succeeded_folders)} items deleted, {len(failed)} failed.",
        )

    @classmethod
    def batch_restore(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        folder_ids: List[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> BatchOperationResult:
        """Bulk restore files and folders from trash."""
        cls.validate_batch_size(file_ids, folder_ids)
        succeeded_files: List[uuid.UUID] = []
        succeeded_folders: List[uuid.UUID] = []
        failed: List[BatchFailureDetail] = []

        # Process folders
        for fid in folder_ids:
            try:
                FolderService.restore_folder(db=db, folder_id=fid, user_id=user_id, ip_address=ip_address)
                succeeded_folders.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="folder", reason=str(detail)))

        # Process files
        for fid in file_ids:
            try:
                FileService.restore_file(db=db, file_id=fid, user_id=user_id, ip_address=ip_address)
                succeeded_files.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="file", reason=str(detail)))

        return BatchOperationResult(
            succeeded_files=succeeded_files,
            succeeded_folders=succeeded_folders,
            failed=failed,
            total_succeeded=len(succeeded_files) + len(succeeded_folders),
            total_failed=len(failed),
            message=f"Batch restore: {len(succeeded_files) + len(succeeded_folders)} items restored, {len(failed)} failed.",
        )

    @classmethod
    def batch_purge(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        folder_ids: List[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> BatchOperationResult:
        """Bulk permanent hard-delete of files and folders."""
        cls.validate_batch_size(file_ids, folder_ids)
        succeeded_files: List[uuid.UUID] = []
        succeeded_folders: List[uuid.UUID] = []
        failed: List[BatchFailureDetail] = []

        for fid in folder_ids:
            try:
                FolderService.hard_delete_folder(db=db, folder_id=fid, user_id=user_id, ip_address=ip_address)
                succeeded_folders.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="folder", reason=str(detail)))

        for fid in file_ids:
            try:
                FileService.hard_delete_file(db=db, file_id=fid, user_id=user_id, ip_address=ip_address)
                succeeded_files.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="file", reason=str(detail)))

        return BatchOperationResult(
            succeeded_files=succeeded_files,
            succeeded_folders=succeeded_folders,
            failed=failed,
            total_succeeded=len(succeeded_files) + len(succeeded_folders),
            total_failed=len(failed),
            message=f"Batch purge: {len(succeeded_files) + len(succeeded_folders)} items permanently deleted, {len(failed)} failed.",
        )

    @classmethod
    def batch_move(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        folder_ids: List[uuid.UUID],
        destination_folder_id: Optional[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> BatchOperationResult:
        """Bulk move files and folders to destination folder."""
        cls.validate_batch_size(file_ids, folder_ids)
        succeeded_files: List[uuid.UUID] = []
        succeeded_folders: List[uuid.UUID] = []
        failed: List[BatchFailureDetail] = []

        # Validate destination folder if not root
        if destination_folder_id is not None:
            dest = db.scalars(
                select(Folder).where(
                    Folder.id == destination_folder_id,
                    Folder.owner_id == user_id,
                    Folder.is_deleted.is_(False),
                )
            ).first()
            if not dest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Destination folder not found.",
                )

        # Move folders
        for fid in folder_ids:
            try:
                FolderService.move_folder(
                    db=db,
                    folder_id=fid,
                    user_id=user_id,
                    destination_parent_id=destination_folder_id,
                    ip_address=ip_address,
                )
                succeeded_folders.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="folder", reason=str(detail)))

        # Move files
        for fid in file_ids:
            try:
                FileService.move_file(
                    db=db,
                    file_id=fid,
                    user_id=user_id,
                    destination_folder_id=destination_folder_id,
                    ip_address=ip_address,
                )
                succeeded_files.append(fid)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="file", reason=str(detail)))

        return BatchOperationResult(
            succeeded_files=succeeded_files,
            succeeded_folders=succeeded_folders,
            failed=failed,
            total_succeeded=len(succeeded_files) + len(succeeded_folders),
            total_failed=len(failed),
            message=f"Batch move: {len(succeeded_files) + len(succeeded_folders)} items moved, {len(failed)} failed.",
        )

    @classmethod
    def batch_copy(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        destination_folder_id: Optional[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> BatchOperationResult:
        """Bulk duplicate/copy files to destination folder."""
        if not file_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch copy request must contain at least one file ID.",
            )
        if len(file_ids) > settings.MAX_BATCH_OPERATION_ITEMS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch copy exceeds maximum allowed items ({settings.MAX_BATCH_OPERATION_ITEMS}).",
            )

        succeeded_files: List[uuid.UUID] = []
        failed: List[BatchFailureDetail] = []

        for fid in file_ids:
            try:
                new_file = FileService.copy_file(
                    db=db,
                    file_id=fid,
                    user_id=user_id,
                    destination_folder_id=destination_folder_id,
                    ip_address=ip_address,
                )
                succeeded_files.append(new_file.id)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                failed.append(BatchFailureDetail(id=fid, resource_type="file", reason=str(detail)))

        return BatchOperationResult(
            succeeded_files=succeeded_files,
            succeeded_folders=[],
            failed=failed,
            total_succeeded=len(succeeded_files),
            total_failed=len(failed),
            message=f"Batch copy: {len(succeeded_files)} files copied, {len(failed)} failed.",
        )

    @classmethod
    def batch_star(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        folder_ids: List[uuid.UUID],
        is_starred: bool,
    ) -> BatchOperationResult:
        """Bulk star or unstar files and folders."""
        cls.validate_batch_size(file_ids, folder_ids)
        succeeded_files: List[uuid.UUID] = []
        succeeded_folders: List[uuid.UUID] = []
        failed: List[BatchFailureDetail] = []

        # Process folders
        for fid in folder_ids:
            try:
                folder = db.scalars(
                    select(Folder).where(Folder.id == fid, Folder.owner_id == user_id, Folder.is_deleted.is_(False))
                ).first()
                if not folder:
                    failed.append(BatchFailureDetail(id=fid, resource_type="folder", reason="Folder not found."))
                    continue

                star = db.scalars(
                    select(Star).where(Star.user_id == user_id, Star.folder_id == fid)
                ).first()

                if is_starred and not star:
                    db.add(Star(user_id=user_id, folder_id=fid))
                elif not is_starred and star:
                    db.delete(star)

                succeeded_folders.append(fid)
            except Exception as exc:
                failed.append(BatchFailureDetail(id=fid, resource_type="folder", reason=str(exc)))

        # Process files
        for fid in file_ids:
            try:
                file = db.scalars(
                    select(File).where(File.id == fid, File.owner_id == user_id, File.is_deleted.is_(False))
                ).first()
                if not file:
                    failed.append(BatchFailureDetail(id=fid, resource_type="file", reason="File not found."))
                    continue

                star = db.scalars(
                    select(Star).where(Star.user_id == user_id, Star.file_id == fid)
                ).first()

                if is_starred and not star:
                    db.add(Star(user_id=user_id, file_id=fid))
                elif not is_starred and star:
                    db.delete(star)

                succeeded_files.append(fid)
            except Exception as exc:
                failed.append(BatchFailureDetail(id=fid, resource_type="file", reason=str(exc)))

        db.commit()

        return BatchOperationResult(
            succeeded_files=succeeded_files,
            succeeded_folders=succeeded_folders,
            failed=failed,
            total_succeeded=len(succeeded_files) + len(succeeded_folders),
            total_failed=len(failed),
            message=f"Batch star: {len(succeeded_files) + len(succeeded_folders)} items updated.",
        )

    @classmethod
    def create_zip_archive(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_ids: List[uuid.UUID],
        folder_ids: List[uuid.UUID],
    ) -> io.BytesIO:
        """Dynamically assemble and compress selected files and folders into an in-memory ZIP archive."""
        cls.validate_batch_size(file_ids, folder_ids)

        zip_buffer = io.BytesIO()
        total_uncompressed_bytes = 0

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Process explicit top-level files
            used_root_filenames: Set[str] = set()
            for fid in file_ids:
                file = db.scalars(
                    select(File).where(File.id == fid, File.owner_id == user_id, File.is_deleted.is_(False))
                ).first()
                if not file:
                    continue

                content = StorageService.get_file_bytes(file.storage_path) or b""
                total_uncompressed_bytes += len(content)
                if total_uncompressed_bytes > settings.MAX_ZIP_DOWNLOAD_BYTES:
                    raise HTTPException(
                                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                        detail=f"Total download size exceeds max archive limit ({settings.MAX_ZIP_DOWNLOAD_BYTES} bytes).",
                    )

                # Deduplicate name if needed
                arcname = file.name
                counter = 1
                while arcname in used_root_filenames:
                    name_part, ext_part = (file.name.rsplit(".", 1) + [""])[:2]
                    arcname = f"{name_part}_{counter}.{ext_part}" if ext_part else f"{name_part}_{counter}"
                    counter += 1
                used_root_filenames.add(arcname)

                zip_file.writestr(arcname, content)

            # 2. Process folders recursively
            for folder_id in folder_ids:
                root_folder = db.scalars(
                    select(Folder).where(
                        Folder.id == folder_id,
                        Folder.owner_id == user_id,
                        Folder.is_deleted.is_(False),
                    )
                ).first()
                if not root_folder:
                    continue

                # Recursive walk helper
                def add_folder_to_zip(current_folder: Folder, base_path: str) -> None:
                    nonlocal total_uncompressed_bytes
                    current_path = f"{base_path}/{current_folder.name}" if base_path else current_folder.name

                    # Add empty directory entry
                    zip_file.writestr(f"{current_path}/", b"")

                    # Add files in current folder
                    folder_files = db.scalars(
                        select(File).where(
                            File.folder_id == current_folder.id,
                            File.owner_id == user_id,
                            File.is_deleted.is_(False),
                        )
                    ).all()

                    for ff in folder_files:
                        data = StorageService.get_file_bytes(ff.storage_path) or b""
                        total_uncompressed_bytes += len(data)
                        if total_uncompressed_bytes > settings.MAX_ZIP_DOWNLOAD_BYTES:
                            raise HTTPException(
                                        status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                                detail="Total download size exceeds max archive limit.",
                            )
                        zip_file.writestr(f"{current_path}/{ff.name}", data)

                    # Subfolders
                    subfolders = db.scalars(
                        select(Folder).where(
                            Folder.parent_id == current_folder.id,
                            Folder.owner_id == user_id,
                            Folder.is_deleted.is_(False),
                        )
                    ).all()

                    for sub in subfolders:
                        add_folder_to_zip(sub, current_path)

                add_folder_to_zip(root_folder, "")

        zip_buffer.seek(0)
        return zip_buffer
