"""File management service handling upload flows, versioning, downloads, moves, copies, and stars."""

from datetime import datetime, timezone
from typing import List, Optional, Set, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.file_version import FileVersion
from app.models.folder import Folder
from app.models.star import Star
from app.models.user import User
from app.schemas.file import (
    FileCopy,
    FileDetailResponse,
    FileDownloadResponse,
    FileListResponse,
    FileMove,
    FileResponse,
    FileUpdate,
    FileUploadComplete,
    FileUploadInit,
    FileUploadInitResponse,
    FileVersionComplete,
    FileVersionInit,
    FileVersionInitResponse,
    FileVersionResponse,
)
from app.services.activity_service import ActivityService
from app.services.folder_service import FolderService
from app.services.storage_service import StorageService


class FileService:
    """Business logic service for file storage, versions, metadata, and lifecycle."""

    @staticmethod
    def get_file_by_id(
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> File:
        """Retrieve a file ensuring it belongs to the authenticated user."""
        query = select(File).where(File.id == file_id, File.owner_id == user_id)
        if not include_deleted:
            query = query.where(File.is_deleted.is_(False))

        file = db.scalars(query).first()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            )
        return file

    @staticmethod
    def is_file_starred(db: Session, file_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check whether a file is starred by the user."""
        star = db.scalars(
            select(Star).where(Star.user_id == user_id, Star.file_id == file_id)
        ).first()
        return star is not None

    @staticmethod
    def get_starred_file_ids(db: Session, user_id: uuid.UUID) -> Set[uuid.UUID]:
        """Fetch all starred file UUIDs for a given user."""
        stmt = select(Star.file_id).where(Star.user_id == user_id, Star.file_id.is_not(None))
        return set(db.scalars(stmt).all())

    @staticmethod
    def get_current_version_number(db: Session, file_id: uuid.UUID) -> int:
        """Get the highest active version number for a file."""
        max_ver = db.scalar(
            select(func.max(FileVersion.version_number)).where(FileVersion.file_id == file_id)
        )
        return max_ver if max_ver is not None else 1

    @classmethod
    def to_file_response(
        cls,
        db: Session,
        file: File,
        user_id: uuid.UUID,
        is_starred: Optional[bool] = None,
    ) -> FileResponse:
        """Helper to convert File ORM model to FileResponse schema."""
        if is_starred is None:
            is_starred = cls.is_file_starred(db, file.id, user_id)
        current_version_number = cls.get_current_version_number(db, file.id)

        return FileResponse(
            id=file.id,
            name=file.name,
            folder_id=file.folder_id,
            owner_id=file.owner_id,
            mime_type=file.mime_type,
            size_bytes=file.size_bytes,
            storage_path=file.storage_path,
            is_deleted=file.is_deleted,
            deleted_at=file.deleted_at,
            created_at=file.created_at,
            updated_at=file.updated_at,
            is_starred=is_starred,
            current_version_number=current_version_number,
        )

    @classmethod
    def get_file_detail(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> FileDetailResponse:
        """Fetch detailed file metadata, navigation breadcrumbs, and version history."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)
        is_starred = cls.is_file_starred(db=db, file_id=file.id, user_id=user_id)
        breadcrumbs = FolderService.get_folder_breadcrumbs(db=db, folder_id=file.folder_id, user_id=user_id)

        versions_stmt = (
            select(FileVersion)
            .where(FileVersion.file_id == file.id)
            .order_by(FileVersion.version_number.desc())
        )
        versions_orm = db.scalars(versions_stmt).all()
        versions_list = [FileVersionResponse.model_validate(v) for v in versions_orm]

        current_ver = versions_list[0].version_number if versions_list else 1

        return FileDetailResponse(
            id=file.id,
            name=file.name,
            folder_id=file.folder_id,
            owner_id=file.owner_id,
            mime_type=file.mime_type,
            size_bytes=file.size_bytes,
            storage_path=file.storage_path,
            is_deleted=file.is_deleted,
            deleted_at=file.deleted_at,
            created_at=file.created_at,
            updated_at=file.updated_at,
            is_starred=is_starred,
            current_version_number=current_ver,
            breadcrumbs=breadcrumbs,
            versions=versions_list,
            versions_count=len(versions_list),
        )

    @classmethod
    def init_upload(
        cls,
        db: Session,
        user_id: uuid.UUID,
        init_in: FileUploadInit,
        ip_address: Optional[str] = None,
    ) -> FileUploadInitResponse:
        """Initiate presigned upload flow by creating pending metadata and signed URL."""
        # Validate storage quota
        from app.services.storage_analytics_service import StorageAnalyticsService
        StorageAnalyticsService.validate_quota_available(db=db, user_id=user_id, incoming_bytes=init_in.size_bytes)

        # 1. Validate parent folder if specified
        if init_in.folder_id is not None:
            parent = FolderService.get_folder_by_id(
                db=db,
                folder_id=init_in.folder_id,
                user_id=user_id,
                include_deleted=False,
            )
            if parent.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found.",
                )

        # 2. Check for duplicate sibling name
        duplicate_query = select(File).where(
            File.owner_id == user_id,
            File.folder_id == init_in.folder_id,
            File.is_deleted.is_(False),
            func.lower(File.name) == init_in.name.lower(),
        )
        if db.scalars(duplicate_query).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file named '{init_in.name}' already exists in this location.",
            )

        # 3. Generate IDs and storage path
        file_id = uuid.uuid4()
        clean_name = StorageService.sanitize_filename(init_in.name)
        storage_path = StorageService.generate_storage_path(
            user_id=user_id,
            file_id=file_id,
            version_number=1,
            filename=clean_name,
        )

        # 4. Create initial File entity
        file = File(
            id=file_id,
            name=clean_name,
            folder_id=init_in.folder_id,
            owner_id=user_id,
            mime_type=init_in.mime_type,
            size_bytes=init_in.size_bytes,
            storage_path=storage_path,
        )
        db.add(file)
        db.flush()

        # 5. Generate Presigned Upload URL
        upload_info = StorageService.generate_presigned_upload_url(storage_path=storage_path)

        # 6. Audit logging
        ActivityService.log_activity(
            db=db,
            action="FILE_UPLOAD_INIT",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={
                "name": file.name,
                "folder_id": str(file.folder_id) if file.folder_id else None,
                "size_bytes": file.size_bytes,
                "storage_path": storage_path,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)

        return FileUploadInitResponse(
            file_id=file.id,
            version_number=1,
            storage_path=storage_path,
            upload_url=upload_info["upload_url"],
            expires_in_seconds=upload_info["expires_in_seconds"],
            method=upload_info["method"],
        )

    @classmethod
    def complete_upload(
        cls,
        db: Session,
        user_id: uuid.UUID,
        complete_in: FileUploadComplete,
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Confirm direct/presigned upload completion and register Version 1."""
        file = cls.get_file_by_id(db=db, file_id=complete_in.file_id, user_id=user_id, include_deleted=False)

        # If actual size differs, update file size
        final_size = complete_in.actual_size_bytes if complete_in.actual_size_bytes is not None else file.size_bytes
        file.size_bytes = final_size

        # Check if version 1 already created
        ver1 = db.scalars(
            select(FileVersion).where(
                FileVersion.file_id == file.id,
                FileVersion.version_number == 1,
            )
        ).first()

        if not ver1:
            ver1 = FileVersion(
                file_id=file.id,
                version_number=1,
                storage_path=file.storage_path,
                size_bytes=final_size,
                mime_type=file.mime_type,
                checksum_sha256=complete_in.checksum_sha256,
                uploaded_by_id=user_id,
            )
            db.add(ver1)

            # Update User quota
            user = db.get(User, user_id)
            if user:
                user.storage_used_bytes += final_size

        # Audit activity
        ActivityService.log_activity(
            db=db,
            action="FILE_UPLOAD_COMPLETE",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={
                "name": file.name,
                "version_number": 1,
                "size_bytes": final_size,
                "checksum": complete_in.checksum_sha256,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return cls.to_file_response(db=db, file=file, user_id=user_id)

    @classmethod
    def direct_upload(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        folder_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Direct multipart binary file upload creating File and FileVersion v1."""
        # Validate storage quota
        from app.services.storage_analytics_service import StorageAnalyticsService
        StorageAnalyticsService.validate_quota_available(db=db, user_id=user_id, incoming_bytes=len(file_bytes))

        # 1. Validate parent folder if specified
        if folder_id is not None:
            parent = FolderService.get_folder_by_id(
                db=db,
                folder_id=folder_id,
                user_id=user_id,
                include_deleted=False,
            )
            if parent.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found.",
                )

        clean_name = StorageService.sanitize_filename(filename)

        # 2. Check for duplicate sibling name
        duplicate_query = select(File).where(
            File.owner_id == user_id,
            File.folder_id == folder_id,
            File.is_deleted.is_(False),
            func.lower(File.name) == clean_name.lower(),
        )
        if db.scalars(duplicate_query).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file named '{clean_name}' already exists in this location.",
            )

        # 3. Create ID and storage path
        file_id = uuid.uuid4()
        size_bytes = len(file_bytes)
        storage_path = StorageService.generate_storage_path(
            user_id=user_id,
            file_id=file_id,
            version_number=1,
            filename=clean_name,
        )

        # 4. Save binary bytes to storage provider
        StorageService.save_file_bytes(storage_path=storage_path, file_bytes=file_bytes)
        checksum = StorageService.compute_checksum_sha256(file_bytes=file_bytes)

        # 5. Create File entity
        file = File(
            id=file_id,
            name=clean_name,
            folder_id=folder_id,
            owner_id=user_id,
            mime_type=mime_type or "application/octet-stream",
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        db.add(file)
        db.flush()

        # 6. Create FileVersion 1
        ver1 = FileVersion(
            file_id=file.id,
            version_number=1,
            storage_path=storage_path,
            size_bytes=size_bytes,
            mime_type=file.mime_type,
            checksum_sha256=checksum,
            uploaded_by_id=user_id,
        )
        db.add(ver1)

        # 7. Update User quota
        user = db.get(User, user_id)
        if user:
            user.storage_used_bytes += size_bytes

        # 8. Activity log
        ActivityService.log_activity(
            db=db,
            action="FILE_UPLOAD",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={
                "name": file.name,
                "folder_id": str(folder_id) if folder_id else None,
                "size_bytes": size_bytes,
                "checksum": checksum,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return cls.to_file_response(db=db, file=file, user_id=user_id)

    @classmethod
    def init_version_upload(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        version_in: FileVersionInit,
        ip_address: Optional[str] = None,
    ) -> FileVersionInitResponse:
        """Initiate presigned upload for a new version of an existing file."""
        from app.services.storage_analytics_service import StorageAnalyticsService
        StorageAnalyticsService.validate_quota_available(db=db, user_id=user_id, incoming_bytes=version_in.size_bytes)

        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)
        next_ver = cls.get_current_version_number(db, file.id) + 1

        storage_path = StorageService.generate_storage_path(
            user_id=user_id,
            file_id=file.id,
            version_number=next_ver,
            filename=file.name,
        )
        upload_info = StorageService.generate_presigned_upload_url(storage_path=storage_path)

        return FileVersionInitResponse(
            file_id=file.id,
            version_number=next_ver,
            storage_path=storage_path,
            upload_url=upload_info["upload_url"],
            expires_in_seconds=upload_info["expires_in_seconds"],
            method=upload_info["method"],
        )

    @classmethod
    def complete_version_upload(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        complete_in: FileVersionComplete,
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Confirm completion of new version upload and promote it to active version."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)
        target_ver = complete_in.version_number

        storage_path = StorageService.generate_storage_path(
            user_id=user_id,
            file_id=file.id,
            version_number=target_ver,
            filename=file.name,
        )
        size_bytes = complete_in.actual_size_bytes if complete_in.actual_size_bytes is not None else file.size_bytes

        ver = FileVersion(
            file_id=file.id,
            version_number=target_ver,
            storage_path=storage_path,
            size_bytes=size_bytes,
            mime_type=file.mime_type,
            checksum_sha256=complete_in.checksum_sha256,
            uploaded_by_id=user_id,
        )
        db.add(ver)

        # Update active file pointer
        file.storage_path = storage_path
        file.size_bytes = size_bytes

        # Update user quota
        user = db.get(User, user_id)
        if user:
            user.storage_used_bytes += size_bytes

        ActivityService.log_activity(
            db=db,
            action="FILE_VERSION_UPLOAD",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={
                "name": file.name,
                "version_number": target_ver,
                "size_bytes": size_bytes,
                "checksum": complete_in.checksum_sha256,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return cls.to_file_response(db=db, file=file, user_id=user_id)

    @classmethod
    def direct_upload_version(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        file_bytes: bytes,
        mime_type: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Direct multipart upload for a new version of an existing file."""
        from app.services.storage_analytics_service import StorageAnalyticsService
        StorageAnalyticsService.validate_quota_available(db=db, user_id=user_id, incoming_bytes=len(file_bytes))

        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)
        next_ver = cls.get_current_version_number(db, file.id) + 1

        size_bytes = len(file_bytes)
        storage_path = StorageService.generate_storage_path(
            user_id=user_id,
            file_id=file.id,
            version_number=next_ver,
            filename=file.name,
        )

        StorageService.save_file_bytes(storage_path=storage_path, file_bytes=file_bytes)
        checksum = StorageService.compute_checksum_sha256(file_bytes=file_bytes)
        effective_mime = mime_type or file.mime_type

        ver = FileVersion(
            file_id=file.id,
            version_number=next_ver,
            storage_path=storage_path,
            size_bytes=size_bytes,
            mime_type=effective_mime,
            checksum_sha256=checksum,
            uploaded_by_id=user_id,
        )
        db.add(ver)

        file.storage_path = storage_path
        file.size_bytes = size_bytes
        file.mime_type = effective_mime

        user = db.get(User, user_id)
        if user:
            user.storage_used_bytes += size_bytes

        ActivityService.log_activity(
            db=db,
            action="FILE_VERSION_UPLOAD",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={
                "name": file.name,
                "version_number": next_ver,
                "size_bytes": size_bytes,
                "checksum": checksum,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return cls.to_file_response(db=db, file=file, user_id=user_id)

    @classmethod
    def get_download_url(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        version_number: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> FileDownloadResponse:
        """Generate presigned download URL for latest or specific file version."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)

        if version_number is not None:
            ver = db.scalars(
                select(FileVersion).where(
                    FileVersion.file_id == file.id,
                    FileVersion.version_number == version_number,
                )
            ).first()
            if not ver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File version {version_number} not found.",
                )
            storage_path = ver.storage_path
            size_bytes = ver.size_bytes
            mime_type = ver.mime_type
            v_num = ver.version_number
        else:
            storage_path = file.storage_path
            size_bytes = file.size_bytes
            mime_type = file.mime_type
            v_num = cls.get_current_version_number(db, file.id)

        download_url = StorageService.generate_presigned_download_url(
            storage_path=storage_path,
            filename=file.name,
        )

        ActivityService.log_activity(
            db=db,
            action="FILE_DOWNLOAD",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"version_number": v_num, "name": file.name},
            ip_address=ip_address,
        )
        db.commit()

        return FileDownloadResponse(
            download_url=download_url,
            file_id=file.id,
            name=file.name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            version_number=v_num,
            expires_in_seconds=3600,
        )

    @classmethod
    def get_file_stream(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        version_number: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """Fetch binary content, filename, and MIME type for direct streaming."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)

        if version_number is not None:
            ver = db.scalars(
                select(FileVersion).where(
                    FileVersion.file_id == file.id,
                    FileVersion.version_number == version_number,
                )
            ).first()
            if not ver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File version {version_number} not found.",
                )
            storage_path = ver.storage_path
            mime_type = ver.mime_type
            v_num = ver.version_number
        else:
            storage_path = file.storage_path
            mime_type = file.mime_type
            v_num = cls.get_current_version_number(db, file.id)

        data = StorageService.get_file_bytes(storage_path) or b""

        ActivityService.log_activity(
            db=db,
            action="FILE_DOWNLOAD",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"version_number": v_num, "name": file.name, "stream": True},
            ip_address=ip_address,
        )
        db.commit()

        return data, file.name, mime_type

    @classmethod
    def list_file_versions(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[FileVersionResponse]:
        """List all version snapshots for a file."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)
        versions_stmt = (
            select(FileVersion)
            .where(FileVersion.file_id == file.id)
            .order_by(FileVersion.version_number.desc())
        )
        versions_orm = db.scalars(versions_stmt).all()
        return [FileVersionResponse.model_validate(v) for v in versions_orm]

    @classmethod
    def update_file(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        update_in: FileUpdate,
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Rename file with sibling conflict validation."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)
        clean_name = StorageService.sanitize_filename(update_in.name)

        if clean_name.lower() != file.name.lower():
            dup = db.scalars(
                select(File).where(
                    File.owner_id == user_id,
                    File.folder_id == file.folder_id,
                    File.is_deleted.is_(False),
                    func.lower(File.name) == clean_name.lower(),
                )
            ).first()
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A file named '{clean_name}' already exists in this location.",
                )

        old_name = file.name
        file.name = clean_name

        ActivityService.log_activity(
            db=db,
            action="FILE_RENAME",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"old_name": old_name, "new_name": clean_name},
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return cls.to_file_response(db=db, file=file, user_id=user_id)

    @classmethod
    def move_file(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        destination_folder_id: Optional[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Relocate file to target destination directory."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)

        if destination_folder_id == file.folder_id:
            return cls.to_file_response(db=db, file=file, user_id=user_id)

        if destination_folder_id is not None:
            parent = FolderService.get_folder_by_id(
                db=db,
                folder_id=destination_folder_id,
                user_id=user_id,
                include_deleted=False,
            )
            if parent.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Destination folder not found.",
                )

        # Check duplicate name in destination
        dup = db.scalars(
            select(File).where(
                File.owner_id == user_id,
                File.folder_id == destination_folder_id,
                File.is_deleted.is_(False),
                func.lower(File.name) == file.name.lower(),
            )
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file named '{file.name}' already exists in the destination folder.",
            )

        old_folder_id = file.folder_id
        file.folder_id = destination_folder_id

        ActivityService.log_activity(
            db=db,
            action="FILE_MOVE",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={
                "old_folder_id": str(old_folder_id) if old_folder_id else None,
                "new_folder_id": str(destination_folder_id) if destination_folder_id else None,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return cls.to_file_response(db=db, file=file, user_id=user_id)

    @classmethod
    def copy_file(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        destination_folder_id: Optional[uuid.UUID] = None,
        new_name: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> FileResponse:
        """Duplicate a file to destination folder, cloning storage blob and updating quota."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)

        dest_folder_id = destination_folder_id if destination_folder_id is not None else file.folder_id
        if dest_folder_id is not None:
            parent = FolderService.get_folder_by_id(
                db=db,
                folder_id=dest_folder_id,
                user_id=user_id,
                include_deleted=False,
            )
            if parent.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Destination folder not found.",
                )

        target_name = StorageService.sanitize_filename(new_name) if new_name else f"Copy of {file.name}"

        # Sibling duplicate check
        dup = db.scalars(
            select(File).where(
                File.owner_id == user_id,
                File.folder_id == dest_folder_id,
                File.is_deleted.is_(False),
                func.lower(File.name) == target_name.lower(),
            )
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file named '{target_name}' already exists in the destination folder.",
            )

        new_file_id = uuid.uuid4()
        new_storage_path = StorageService.generate_storage_path(
            user_id=user_id,
            file_id=new_file_id,
            version_number=1,
            filename=target_name,
        )

        # Clone binary blob in storage
        orig_bytes = StorageService.get_file_bytes(file.storage_path)
        if orig_bytes is not None:
            StorageService.save_file_bytes(new_storage_path, orig_bytes)

        # Create new File
        new_file = File(
            id=new_file_id,
            name=target_name,
            folder_id=dest_folder_id,
            owner_id=user_id,
            mime_type=file.mime_type,
            size_bytes=file.size_bytes,
            storage_path=new_storage_path,
        )
        db.add(new_file)
        db.flush()

        # Create FileVersion 1
        new_ver = FileVersion(
            file_id=new_file.id,
            version_number=1,
            storage_path=new_storage_path,
            size_bytes=file.size_bytes,
            mime_type=file.mime_type,
            uploaded_by_id=user_id,
        )
        db.add(new_ver)

        # Update User quota
        user = db.get(User, user_id)
        if user:
            user.storage_used_bytes += file.size_bytes

        ActivityService.log_activity(
            db=db,
            action="FILE_COPY",
            resource_type="FILE",
            resource_id=new_file.id,
            user_id=user_id,
            details={
                "source_file_id": str(file.id),
                "new_file_id": str(new_file.id),
                "destination_folder_id": str(dest_folder_id) if dest_folder_id else None,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(new_file)
        return cls.to_file_response(db=db, file=new_file, user_id=user_id)

    @classmethod
    def toggle_star(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Toggle starred favorite status for a file."""
        cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)

        star = db.scalars(
            select(Star).where(Star.user_id == user_id, Star.file_id == file_id)
        ).first()

        if star:
            db.delete(star)
            is_starred = False
            action = "FILE_UNSTAR"
        else:
            new_star = Star(user_id=user_id, file_id=file_id)
            db.add(new_star)
            is_starred = True
            action = "FILE_STAR"

        ActivityService.log_activity(
            db=db,
            action=action,
            resource_type="FILE",
            resource_id=file_id,
            user_id=user_id,
        )

        db.commit()
        return is_starred

    @classmethod
    def soft_delete_file(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> File:
        """Soft delete file moving it to Trash."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=False)

        file.is_deleted = True
        file.deleted_at = datetime.now(timezone.utc)

        # Remove star if starred
        stars = db.scalars(select(Star).where(Star.file_id == file.id)).all()
        for s in stars:
            db.delete(s)

        ActivityService.log_activity(
            db=db,
            action="FILE_TRASH",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"name": file.name},
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return file

    @classmethod
    def restore_file(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> File:
        """Restore soft-deleted file from Trash."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=True)
        if not file.is_deleted:
            return file

        # If parent folder is soft-deleted or does not exist, move to Root
        if file.folder_id is not None:
            parent = db.scalars(
                select(Folder).where(Folder.id == file.folder_id, Folder.owner_id == user_id)
            ).first()
            if not parent or parent.is_deleted:
                file.folder_id = None

        # Check for active sibling duplicate
        dup = db.scalars(
            select(File).where(
                File.owner_id == user_id,
                File.folder_id == file.folder_id,
                File.is_deleted.is_(False),
                func.lower(File.name) == file.name.lower(),
            )
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file named '{file.name}' already exists in this folder. Rename or delete the existing file before restoring.",
            )

        file.is_deleted = False
        file.deleted_at = None

        ActivityService.log_activity(
            db=db,
            action="FILE_RESTORE",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"name": file.name},
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(file)
        return file

    @classmethod
    def hard_delete_file(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Permanently delete file, versions, and storage blobs; decrement user quota."""
        file = cls.get_file_by_id(db=db, file_id=file_id, user_id=user_id, include_deleted=True)

        # Retrieve all versions for total size calculation and storage purging
        versions = db.scalars(select(FileVersion).where(FileVersion.file_id == file.id)).all()
        total_freed_bytes = sum(v.size_bytes for v in versions) if versions else file.size_bytes

        for v in versions:
            StorageService.delete_file_bytes(v.storage_path)
        StorageService.delete_file_bytes(file.storage_path)

        user = db.get(User, user_id)
        if user:
            user.storage_used_bytes = max(0, user.storage_used_bytes - total_freed_bytes)

        ActivityService.log_activity(
            db=db,
            action="FILE_PERMANENT_DELETE",
            resource_type="FILE",
            resource_id=file.id,
            user_id=user_id,
            details={"name": file.name, "freed_bytes": total_freed_bytes},
            ip_address=ip_address,
        )

        db.delete(file)
        db.commit()

    @classmethod
    def list_starred_files(
        cls,
        db: Session,
        user_id: uuid.UUID,
    ) -> List[FileResponse]:
        """Fetch all starred active files for the authenticated user."""
        stmt = (
            select(File)
            .join(Star, Star.file_id == File.id)
            .where(
                Star.user_id == user_id,
                File.owner_id == user_id,
                File.is_deleted.is_(False),
            )
            .order_by(File.name.asc())
        )
        files = db.scalars(stmt).all()
        return [cls.to_file_response(db=db, file=f, user_id=user_id, is_starred=True) for f in files]

    @classmethod
    def list_trash_files(
        cls,
        db: Session,
        user_id: uuid.UUID,
    ) -> List[FileResponse]:
        """Fetch all soft-deleted files for the user."""
        stmt = (
            select(File)
            .where(
                File.owner_id == user_id,
                File.is_deleted.is_(True),
            )
            .order_by(File.deleted_at.desc())
        )
        files = db.scalars(stmt).all()
        return [cls.to_file_response(db=db, file=f, user_id=user_id, is_starred=False) for f in files]

    @classmethod
    def search_files(
        cls,
        db: Session,
        user_id: uuid.UUID,
        query: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder_id: Optional[uuid.UUID] = None,
        is_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> FileListResponse:
        """Search and filter files across properties."""
        base_stmt = select(File).where(
            File.owner_id == user_id,
            File.is_deleted == is_deleted,
        )

        if query:
            base_stmt = base_stmt.where(File.name.ilike(f"%{query.strip()}%"))
        if mime_type:
            base_stmt = base_stmt.where(File.mime_type.ilike(f"%{mime_type.strip()}%"))
        if folder_id is not None:
            base_stmt = base_stmt.where(File.folder_id == folder_id)

        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_count = db.scalar(count_stmt) or 0

        # Fetch page
        paged_stmt = base_stmt.order_by(File.name.asc()).limit(limit).offset(offset)
        files = db.scalars(paged_stmt).all()

        starred_ids = cls.get_starred_file_ids(db=db, user_id=user_id)
        items = [
            cls.to_file_response(db=db, file=f, user_id=user_id, is_starred=(f.id in starred_ids))
            for f in files
        ]

        return FileListResponse(items=items, total_count=total_count)
