"""LinkShare service handling public tokenized links, password hashing, and anonymous downloads."""

from datetime import datetime, timezone
import secrets
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.core.security import hash_password, verify_password
from app.models.file import File
from app.models.folder import Folder
from app.models.link_share import LinkShare
from app.schemas.common import BreadcrumbItem
from app.schemas.file import FileResponse
from app.schemas.folder import FolderResponse
from app.schemas.link_share import (
    LinkShareCreate,
    LinkShareResponse,
    LinkShareUpdate,
    PublicFolderContentsResponse,
    PublicLinkAccessResponse,
)
from app.services.activity_service import ActivityService
from app.services.storage_service import StorageService


class LinkShareService:
    """Business logic for public shareable links and anonymous file/folder consumption."""

    @staticmethod
    def _to_link_response(link: LinkShare) -> LinkShareResponse:
        """Convert a LinkShare ORM model to LinkShareResponse schema."""
        return LinkShareResponse(
            id=link.id,
            token=link.token,
            created_by_id=link.created_by_id,
            file_id=link.file_id,
            folder_id=link.folder_id,
            role=link.role,
            has_password=link.password_hash is not None,
            expires_at=link.expires_at,
            is_active=link.is_active,
            access_count=link.access_count,
            share_url=f"/api/v1/public/links/{link.token}",
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

    @staticmethod
    def create_link_share(
        db: Session,
        user_id: uuid.UUID,
        link_in: LinkShareCreate,
        ip_address: Optional[str] = None,
    ) -> LinkShareResponse:
        """Create a new public share link with optional password and expiry."""
        resource_name = ""
        resource_type = ""
        target_id: uuid.UUID

        if link_in.file_id:
            file = db.scalar(
                select(File).where(File.id == link_in.file_id, File.is_deleted.is_(False))
            )
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found or has been deleted.",
                )
            if file.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can generate public share links.",
                )
            resource_name = file.name
            resource_type = "FILE"
            target_id = file.id
        elif link_in.folder_id:
            folder = db.scalar(
                select(Folder).where(Folder.id == link_in.folder_id, Folder.is_deleted.is_(False))
            )
            if not folder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Folder not found or has been deleted.",
                )
            if folder.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can generate public share links.",
                )
            resource_name = folder.name
            resource_type = "FOLDER"
            target_id = folder.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file_id or folder_id must be provided.",
            )

        # Generate unique token
        token = secrets.token_urlsafe(32)

        # Hash password if provided
        pwd_hash = hash_password(link_in.password) if link_in.password else None

        link = LinkShare(
            token=token,
            created_by_id=user_id,
            file_id=link_in.file_id,
            folder_id=link_in.folder_id,
            role=link_in.role,
            password_hash=pwd_hash,
            expires_at=link_in.expires_at,
            is_active=True,
            access_count=0,
        )
        db.add(link)
        db.commit()
        db.refresh(link)

        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="LINK_SHARE_CREATED",
            resource_type=resource_type,
            resource_id=target_id,
            details={
                "token": token[:8] + "...",
                "has_password": pwd_hash is not None,
                "expires_at": link_in.expires_at.isoformat() if link_in.expires_at else None,
                "role": link_in.role.value,
                "resource_name": resource_name,
            },
            ip_address=ip_address,
        )
        db.commit()

        return LinkShareService._to_link_response(link)

    @staticmethod
    def get_link_share_by_id(db: Session, link_id: uuid.UUID, user_id: uuid.UUID) -> LinkShare:
        """Retrieve a public share link verifying caller ownership."""
        link = db.scalar(select(LinkShare).where(LinkShare.id == link_id))
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public link share not found.",
            )
        if link.created_by_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator can manage this link.",
            )
        return link

    @staticmethod
    def update_link_share(
        db: Session,
        link_id: uuid.UUID,
        user_id: uuid.UUID,
        update_in: LinkShareUpdate,
        ip_address: Optional[str] = None,
    ) -> LinkShareResponse:
        """Update public link configuration (role, password, expiry, active toggle)."""
        link = LinkShareService.get_link_share_by_id(db, link_id=link_id, user_id=user_id)

        if update_in.role is not None:
            link.role = update_in.role
        if update_in.clear_password:
            link.password_hash = None
        elif update_in.password is not None:
            link.password_hash = hash_password(update_in.password)
        if update_in.expires_at is not None:
            link.expires_at = update_in.expires_at
        if update_in.is_active is not None:
            link.is_active = update_in.is_active

        db.commit()
        db.refresh(link)

        target_id = link.file_id or link.folder_id
        resource_type = "FILE" if link.file_id else "FOLDER"
        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="LINK_SHARE_UPDATED",
            resource_type=resource_type,
            resource_id=target_id,  # type: ignore
            details={
                "token": link.token[:8] + "...",
                "is_active": link.is_active,
                "has_password": link.password_hash is not None,
            },
            ip_address=ip_address,
        )
        db.commit()

        return LinkShareService._to_link_response(link)

    @staticmethod
    def revoke_link_share(
        db: Session,
        link_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Revoke and permanently delete a public share link."""
        link = LinkShareService.get_link_share_by_id(db, link_id=link_id, user_id=user_id)
        target_id = link.file_id or link.folder_id
        resource_type = "FILE" if link.file_id else "FOLDER"

        db.delete(link)
        db.commit()

        ActivityService.log_activity(
            db=db,
            user_id=user_id,
            action="LINK_SHARE_DELETED",
            resource_type=resource_type,
            resource_id=target_id,  # type: ignore
            details={"token": link.token[:8] + "..."},
            ip_address=ip_address,
        )
        db.commit()

    @staticmethod
    def list_links_for_resource(
        db: Session,
        user_id: uuid.UUID,
        file_id: Optional[uuid.UUID] = None,
        folder_id: Optional[uuid.UUID] = None,
    ) -> List[LinkShareResponse]:
        """List all public share links created for a file or folder."""
        if file_id:
            file = db.scalar(select(File).where(File.id == file_id))
            if not file or file.is_deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
            if file.owner_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can view links.")
            links = db.scalars(
                select(LinkShare)
                .where(LinkShare.file_id == file_id)
                .order_by(LinkShare.created_at.desc())
            ).all()
        elif folder_id:
            folder = db.scalar(select(Folder).where(Folder.id == folder_id))
            if not folder or folder.is_deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")
            if folder.owner_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can view links.")
            links = db.scalars(
                select(LinkShare)
                .where(LinkShare.folder_id == folder_id)
                .order_by(LinkShare.created_at.desc())
            ).all()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify file_id or folder_id.",
            )

        return [LinkShareService._to_link_response(l) for l in links]

    @staticmethod
    def resolve_public_link(db: Session, token: str) -> LinkShare:
        """Verify token validity, expiration, and active status."""
        link = db.scalar(
            select(LinkShare)
            .options(joinedload(LinkShare.file), joinedload(LinkShare.folder))
            .where(LinkShare.token == token)
        )
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public share link not found or invalid.",
            )
        if not link.is_active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This share link has been deactivated by the owner.",
            )
        if link.expires_at:
            now_utc = datetime.now(timezone.utc)
            # Ensure timezone awareness comparison
            expires_at_aware = link.expires_at if link.expires_at.tzinfo else link.expires_at.replace(tzinfo=timezone.utc)
            if now_utc > expires_at_aware:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="This share link has expired.",
                )

        if link.file and link.file.is_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared file was removed.")
        if link.folder and link.folder.is_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared folder was removed.")

        return link

    @staticmethod
    def access_public_link(
        db: Session,
        token: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> PublicLinkAccessResponse:
        """Inspect and access a public link, handling password authentication and tracking."""
        link = LinkShareService.resolve_public_link(db, token)
        has_password = link.password_hash is not None

        if has_password:
            if not password:
                # Prompt password
                return PublicLinkAccessResponse(
                    token=token,
                    role=link.role,
                    resource_type="file" if link.file_id else "folder",
                    has_password=True,
                    requires_password=True,
                )
            if not verify_password(password, link.password_hash):  # type: ignore
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password for this protected share link.",
                )

        # Increment access count
        link.access_count += 1
        db.commit()

        target_id = link.file_id or link.folder_id
        resource_type = "file" if link.file_id else "folder"

        ActivityService.log_activity(
            db=db,
            user_id=None,
            action="LINK_SHARE_ACCESSED",
            resource_type=resource_type.upper(),
            resource_id=target_id,  # type: ignore
            details={"token": token[:8] + "..."},
            ip_address=ip_address,
        )
        db.commit()

        file_resp: Optional[FileResponse] = None
        folder_resp: Optional[FolderResponse] = None
        download_url: Optional[str] = None

        if link.file:
            from app.services.file_service import FileService

            ver_num = FileService.get_current_version_number(db, link.file.id)
            file_resp = FileResponse(
                id=link.file.id,
                name=link.file.name,
                folder_id=link.file.folder_id,
                owner_id=link.file.owner_id,
                mime_type=link.file.mime_type,
                size_bytes=link.file.size_bytes,
                storage_path=link.file.storage_path,
                is_deleted=link.file.is_deleted,
                deleted_at=link.file.deleted_at,
                created_at=link.file.created_at,
                updated_at=link.file.updated_at,
                is_starred=False,
                current_version_number=ver_num,
            )
            download_url = f"/api/v1/public/links/{token}/download"
        elif link.folder:
            folder_resp = FolderResponse(
                id=link.folder.id,
                name=link.folder.name,
                parent_id=link.folder.parent_id,
                owner_id=link.folder.owner_id,
                color=link.folder.color,
                is_deleted=link.folder.is_deleted,
                deleted_at=link.folder.deleted_at,
                created_at=link.folder.created_at,
                updated_at=link.folder.updated_at,
                is_starred=False,
            )

        return PublicLinkAccessResponse(
            token=token,
            role=link.role,
            resource_type=resource_type,
            has_password=has_password,
            requires_password=False,
            file=file_resp,
            folder=folder_resp,
            download_url=download_url,
        )

    @staticmethod
    def get_public_file(
        db: Session,
        token: str,
        password: Optional[str] = None,
    ) -> File:
        """Resolve public file record, ensuring link is valid and authorized."""
        link = LinkShareService.resolve_public_link(db, token)
        if not link.file_id or not link.file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This share link does not point to a single file.",
            )

        if link.password_hash is not None:
            if not password or not verify_password(password, link.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Valid password required to download this file.",
                )

        return link.file

    @staticmethod
    def get_public_folder_contents(
        db: Session,
        token: str,
        folder_id: Optional[uuid.UUID] = None,
        password: Optional[str] = None,
    ) -> PublicFolderContentsResponse:
        """Browse folder and subfolder contents under a publicly shared folder root."""
        link = LinkShareService.resolve_public_link(db, token)
        if not link.folder_id or not link.folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This share link does not point to a folder.",
            )

        if link.password_hash is not None:
            if not password or not verify_password(password, link.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Valid password required to access this folder.",
                )

        root_folder = link.folder
        target_folder = root_folder

        # If subfolder navigation is requested, ensure target_folder is descendant of root_folder
        if folder_id and folder_id != root_folder.id:
            sub = db.scalar(
                select(Folder).where(Folder.id == folder_id, Folder.is_deleted.is_(False))
            )
            if not sub:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subfolder not found.")

            # Validate that `sub` is indeed inside root_folder
            curr = sub.parent_id
            is_child = False
            while curr:
                if curr == root_folder.id:
                    is_child = True
                    break
                p = db.scalar(select(Folder).where(Folder.id == curr))
                if not p or p.is_deleted:
                    break
                curr = p.parent_id

            if not is_child:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Target folder is outside the scope of this public share.",
                )
            target_folder = sub

        # Fetch child subfolders & files
        subfolders = db.scalars(
            select(Folder)
            .where(Folder.parent_id == target_folder.id, Folder.is_deleted.is_(False))
            .order_by(Folder.name.asc())
        ).all()

        child_files = db.scalars(
            select(File)
            .where(File.folder_id == target_folder.id, File.is_deleted.is_(False))
            .order_by(File.name.asc())
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
            for f in subfolders
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
            for fi in child_files
        ]

        # Breadcrumbs from root_folder down to target_folder
        breadcrumbs: List[BreadcrumbItem] = []
        trail = []
        curr_id = target_folder.id
        while curr_id:
            f = db.scalar(select(Folder).where(Folder.id == curr_id))
            if not f:
                break
            trail.append(BreadcrumbItem(id=f.id, name=f.name))
            if f.id == root_folder.id:
                break
            curr_id = f.parent_id  # type: ignore

        breadcrumbs = list(reversed(trail))

        target_folder_response = FolderResponse(
            id=target_folder.id,
            name=target_folder.name,
            parent_id=target_folder.parent_id,
            owner_id=target_folder.owner_id,
            color=target_folder.color,
            is_deleted=target_folder.is_deleted,
            deleted_at=target_folder.deleted_at,
            created_at=target_folder.created_at,
            updated_at=target_folder.updated_at,
            is_starred=False,
        )

        return PublicFolderContentsResponse(
            folder=target_folder_response,
            breadcrumbs=breadcrumbs,
            folders=folder_responses,
            files=file_responses,
            total_folders=len(folder_responses),
            total_files=len(file_responses),
        )
