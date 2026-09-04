import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.file import File
from app.models.folder import Folder
from app.models.share import Share, ShareRole
from app.models.user import User
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse
from app.schemas.share import (
    ShareCreate,
    SharedByMeResponse,
    SharedItemResponse,
    SharedWithMeResponse,
    ShareResponse,
    ShareUpdate,
)
from app.services.activity_service import ActivityService

class ShareService:
    """Business logic for resource sharing and permission validation."""

    @staticmethod
    def _to_share_response(share: Share) -> ShareResponse:
        """Convert a Share ORM entity to ShareResponse schema."""
        return ShareResponse(
            id=share.id,
            granter_id=share.granter_id,
            granter_email=share.granter.email if share.granter else None,
            granter_name=share.granter.full_name if share.granter else None,
            grantee_id=share.grantee_id,
            grantee_email=share.grantee.email if share.grantee else None,
            grantee_name=share.grantee.full_name if share.grantee else None,
            file_id=share.file_id,
            folder_id=share.folder_id,
            role=share.role,
            created_at=share.created_at,
            updated_at=share.updated_at,
        )

    @staticmethod
    def create_share(
        db: Session,
        granter_id: uuid.UUID,
        share_in: ShareCreate,
        ip_address: Optional[str] = None,
    ) -> ShareResponse:
        """Share a file or folder with another user by email."""

        grantee = db.scalar(
            select(User).where(User.email == share_in.grantee_email.lower().strip())
        )
        if not grantee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{share_in.grantee_email}' was not found.",
            )

        if grantee.id == granter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot share resources with yourself.",
            )

        resource_name = ""
        resource_type = ""
        target_id: uuid.UUID

        if share_in.file_id:
            file = db.scalar(
                select(File).where(File.id == share_in.file_id, File.is_deleted.is_(False))
            )
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target file not found or has been deleted.",
                )
            if file.owner_id != granter_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the file owner can grant sharing permissions.",
                )
            resource_name = file.name
            resource_type = "FILE"
            target_id = file.id
        elif share_in.folder_id:
            folder = db.scalar(
                select(Folder).where(Folder.id == share_in.folder_id, Folder.is_deleted.is_(False))
            )
            if not folder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target folder not found or has been deleted.",
                )
            if folder.owner_id != granter_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the folder owner can grant sharing permissions.",
                )
            resource_name = folder.name
            resource_type = "FOLDER"
            target_id = folder.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file_id or folder_id must be provided.",
            )

        existing_share = db.scalar(
            select(Share)
            .options(joinedload(Share.granter), joinedload(Share.grantee))
            .where(
                Share.grantee_id == grantee.id,
                Share.file_id == share_in.file_id if share_in.file_id else Share.file_id.is_(None),
                Share.folder_id == share_in.folder_id if share_in.folder_id else Share.folder_id.is_(None),
            )
        )

        if existing_share:
            existing_share.role = share_in.role
            db.commit()
            db.refresh(existing_share)

            ActivityService.log_activity(
                db=db,
                user_id=granter_id,
                action="SHARE_UPDATED",
                resource_type=resource_type,
                resource_id=target_id,
                details={
                    "grantee_email": grantee.email,
                    "grantee_id": str(grantee.id),
                    "role": share_in.role.value,
                    "resource_name": resource_name,
                },
                ip_address=ip_address,
            )
            db.commit()
            return ShareService._to_share_response(existing_share)

        new_share = Share(
            granter_id=granter_id,
            grantee_id=grantee.id,
            file_id=share_in.file_id,
            folder_id=share_in.folder_id,
            role=share_in.role,
        )
        db.add(new_share)
        db.commit()
        db.refresh(new_share)

        new_share = db.scalar(
            select(Share)
            .options(joinedload(Share.granter), joinedload(Share.grantee))
            .where(Share.id == new_share.id)
        )

        ActivityService.log_activity(
            db=db,
            user_id=granter_id,
            action="SHARE_GRANTED",
            resource_type=resource_type,
            resource_id=target_id,
            details={
                "grantee_email": grantee.email,
                "grantee_id": str(grantee.id),
                "role": share_in.role.value,
                "resource_name": resource_name,
            },
            ip_address=ip_address,
        )
        db.commit()

        return ShareService._to_share_response(new_share)

    @staticmethod
    def get_share_by_id(db: Session, share_id: uuid.UUID, user_id: uuid.UUID) -> Share:
        """Retrieve a share record verifying user authorization."""
        share = db.scalar(
            select(Share)
            .options(joinedload(Share.granter), joinedload(Share.grantee))
            .where(Share.id == share_id)
        )
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share record not found.",
            )
        if share.granter_id != user_id and share.grantee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this share record.",
            )
        return share

    @staticmethod
    def update_share(
        db: Session,
        share_id: uuid.UUID,
        user_id: uuid.UUID,
        share_update: ShareUpdate,
        ip_address: Optional[str] = None,
    ) -> ShareResponse:
        """Update permission role for a share."""
        share = ShareService.get_share_by_id(db=db, share_id=share_id, user_id=user_id)
        if share.granter_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the granter can update share permissions.",
            )

        share.role = share_update.role
        db.commit()
        db.refresh(share)

        target_id = share.file_id or share.folder_id
        resource_type = "FILE" if share.file_id else "FOLDER"
        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="SHARE_UPDATED",
            resource_type=resource_type,
            resource_id=target_id,
            details={
                "grantee_id": str(share.grantee_id),
                "role": share.role.value,
            },
            ip_address=ip_address,
        )
        db.commit()

        return ShareService._to_share_response(share)

    @staticmethod
    def revoke_share(
        db: Session,
        share_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Revoke a direct share (executable by granter or grantee)."""
        share = ShareService.get_share_by_id(db=db, share_id=share_id, user_id=user_id)

        target_id = share.file_id or share.folder_id
        resource_type = "FILE" if share.file_id else "FOLDER"
        grantee_id = share.grantee_id

        db.delete(share)
        db.commit()

        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="SHARE_REVOKED",
            resource_type=resource_type,
            resource_id=target_id,
            details={
                "grantee_id": str(grantee_id),
            },
            ip_address=ip_address,
        )
        db.commit()

    @staticmethod
    def list_shares_for_resource(
        db: Session,
        user_id: uuid.UUID,
        file_id: Optional[uuid.UUID] = None,
        folder_id: Optional[uuid.UUID] = None,
    ) -> List[ShareResponse]:
        """List all direct shares configured for a specific resource."""
        if file_id:
            file = db.scalar(select(File).where(File.id == file_id))
            if not file or file.is_deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
            if file.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the file owner can view file shares.",
                )
            shares = db.scalars(
                select(Share)
                .options(joinedload(Share.granter), joinedload(Share.grantee))
                .where(Share.file_id == file_id)
                .order_by(Share.created_at.desc())
            ).all()
        elif folder_id:
            folder = db.scalar(select(Folder).where(Folder.id == folder_id))
            if not folder or folder.is_deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")
            if folder.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the folder owner can view folder shares.",
                )
            shares = db.scalars(
                select(Share)
                .options(joinedload(Share.granter), joinedload(Share.grantee))
                .where(Share.folder_id == folder_id)
                .order_by(Share.created_at.desc())
            ).all()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either file_id or folder_id.",
            )

        return [ShareService._to_share_response(s) for s in shares]

    @staticmethod
    def list_shared_with_me(db: Session, user_id: uuid.UUID) -> SharedWithMeResponse:
        """Retrieve all active files and folders shared with the current user."""
        shares = db.scalars(
            select(Share)
            .options(
                joinedload(Share.granter),
                joinedload(Share.file),
                joinedload(Share.folder),
            )
            .where(Share.grantee_id == user_id)
            .order_by(Share.created_at.desc())
        ).all()

        shared_files: List[SharedItemResponse] = []
        shared_folders: List[SharedItemResponse] = []

        from app.services.file_service import FileService
        from app.services.folder_service import FolderService

        starred_file_ids = FileService.get_starred_file_ids(db, user_id)
        starred_folder_ids = FolderService.get_starred_folder_ids(db, user_id)

        for s in shares:
            if s.file and not s.file.is_deleted:
                ver_num = FileService.get_current_version_number(db, s.file.id)
                file_resp = FileResponse(
                    id=s.file.id,
                    name=s.file.name,
                    folder_id=s.file.folder_id,
                    owner_id=s.file.owner_id,
                    mime_type=s.file.mime_type,
                    size_bytes=s.file.size_bytes,
                    storage_path=s.file.storage_path,
                    is_deleted=s.file.is_deleted,
                    deleted_at=s.file.deleted_at,
                    created_at=s.file.created_at,
                    updated_at=s.file.updated_at,
                    is_starred=s.file.id in starred_file_ids,
                    current_version_number=ver_num,
                )
                shared_files.append(
                    SharedItemResponse(
                        share_id=s.id,
                        role=s.role,
                        resource_type="file",
                        file=file_resp,
                        shared_by_id=s.granter_id,
                        shared_by_email=s.granter.email if s.granter else None,
                        shared_by_name=s.granter.full_name if s.granter else None,
                        shared_at=s.created_at,
                    )
                )
            elif s.folder and not s.folder.is_deleted:
                folder_resp = FolderResponse(
                    id=s.folder.id,
                    name=s.folder.name,
                    parent_id=s.folder.parent_id,
                    owner_id=s.folder.owner_id,
                    color=s.folder.color,
                    is_deleted=s.folder.is_deleted,
                    deleted_at=s.folder.deleted_at,
                    created_at=s.folder.created_at,
                    updated_at=s.folder.updated_at,
                    is_starred=s.folder.id in starred_folder_ids,
                )
                shared_folders.append(
                    SharedItemResponse(
                        share_id=s.id,
                        role=s.role,
                        resource_type="folder",
                        folder=folder_resp,
                        shared_by_id=s.granter_id,
                        shared_by_email=s.granter.email if s.granter else None,
                        shared_by_name=s.granter.full_name if s.granter else None,
                        shared_at=s.created_at,
                    )
                )

        return SharedWithMeResponse(
            files=shared_files,
            folders=shared_folders,
            total_count=len(shared_files) + len(shared_folders),
        )

    @staticmethod
    def list_shared_by_me(db: Session, user_id: uuid.UUID) -> SharedByMeResponse:
        """Retrieve all active shares created/granted by the current user."""
        shares = db.scalars(
            select(Share)
            .options(joinedload(Share.granter), joinedload(Share.grantee))
            .where(Share.granter_id == user_id)
            .order_by(Share.created_at.desc())
        ).all()

        results = [ShareService._to_share_response(s) for s in shares]
        return SharedByMeResponse(shares=results, total_count=len(results))

    @staticmethod
    def check_user_access(
        db: Session,
        user_id: uuid.UUID,
        file_id: Optional[uuid.UUID] = None,
        folder_id: Optional[uuid.UUID] = None,
        required_role: ShareRole = ShareRole.VIEWER,
    ) -> Tuple[bool, Optional[str]]:
        """Verify whether a user has permission (Owner or via Direct/Inherited Share).

        Returns:
            (has_access: bool, effective_role: str | None)
            effective_role can be 'OWNER', 'EDITOR', 'VIEWER', or None.
        """
        if file_id:
            file = db.scalar(select(File).where(File.id == file_id))
            if not file or file.is_deleted:
                return False, None

            if file.owner_id == user_id:
                return True, "OWNER"

            share = db.scalar(
                select(Share).where(Share.file_id == file_id, Share.grantee_id == user_id)
            )
            if share:
                if required_role == ShareRole.VIEWER or share.role == ShareRole.EDITOR:
                    return True, share.role.value

            if file.folder_id:
                return ShareService.check_user_access(
                    db=db,
                    user_id=user_id,
                    folder_id=file.folder_id,
                    required_role=required_role,
                )

            return False, None

        if folder_id:
            folder = db.scalar(select(Folder).where(Folder.id == folder_id))
            if not folder or folder.is_deleted:
                return False, None

            if folder.owner_id == user_id:
                return True, "OWNER"

            share = db.scalar(
                select(Share).where(Share.folder_id == folder_id, Share.grantee_id == user_id)
            )
            if share:
                if required_role == ShareRole.VIEWER or share.role == ShareRole.EDITOR:
                    return True, share.role.value

            current_parent_id = folder.parent_id
            while current_parent_id:
                parent_folder = db.scalar(select(Folder).where(Folder.id == current_parent_id))
                if not parent_folder or parent_folder.is_deleted:
                    break

                if parent_folder.owner_id == user_id:
                    return True, "OWNER"

                parent_share = db.scalar(
                    select(Share).where(
                        Share.folder_id == current_parent_id,
                        Share.grantee_id == user_id,
                    )
                )
                if parent_share:
                    if required_role == ShareRole.VIEWER or parent_share.role == ShareRole.EDITOR:
                        return True, parent_share.role.value

                current_parent_id = parent_folder.parent_id

            return False, None

        return False, None
