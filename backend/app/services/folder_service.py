"""Folder management service handling hierarchical directory operations, moves, cascades, and star toggles."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.file import File
from app.models.folder import Folder
from app.models.star import Star
from app.schemas.file import FileResponse
from app.schemas.folder import (
    BreadcrumbItem,
    FolderContentsResponse,
    FolderCreate,
    FolderDetailResponse,
    FolderResponse,
    FolderTreeItem,
    FolderUpdate,
)
from app.services.activity_service import ActivityService


class FolderService:
    """Business logic service for folder hierarchy and management."""

    @staticmethod
    def get_folder_by_id(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Folder:
        """Retrieve a folder ensuring it belongs to the authenticated user."""
        query = select(Folder).where(Folder.id == folder_id, Folder.owner_id == user_id)
        if not include_deleted:
            query = query.where(Folder.is_deleted.is_(False))

        folder = db.scalars(query).first()
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found.",
            )
        return folder

    @staticmethod
    def create_folder(
        db: Session,
        user_id: uuid.UUID,
        folder_in: FolderCreate,
        ip_address: Optional[str] = None,
    ) -> Folder:
        """Create a new folder under a parent directory or at the root level."""
        # 1. Validate parent folder if specified
        if folder_in.parent_id is not None:
            parent = FolderService.get_folder_by_id(
                db=db,
                folder_id=folder_in.parent_id,
                user_id=user_id,
                include_deleted=False,
            )
            if parent.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found.",
                )

        # 2. Check for duplicate sibling name
        duplicate_query = select(Folder).where(
            Folder.owner_id == user_id,
            Folder.parent_id == folder_in.parent_id,
            Folder.is_deleted.is_(False),
            func.lower(Folder.name) == folder_in.name.lower(),
        )
        if db.scalars(duplicate_query).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A folder named '{folder_in.name}' already exists in this location.",
            )

        # 3. Create folder instance
        folder = Folder(
            name=folder_in.name,
            parent_id=folder_in.parent_id,
            owner_id=user_id,
            color=folder_in.color,
        )
        db.add(folder)
        db.flush()

        # 4. Log audit activity
        ActivityService.log_activity(
            db=db,
            action="FOLDER_CREATE",
            resource_type="FOLDER",
            resource_id=folder.id,
            user_id=user_id,
            details={
                "name": folder.name,
                "parent_id": str(folder.parent_id) if folder.parent_id else None,
                "color": folder.color,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def get_folder_breadcrumbs(
        db: Session,
        folder_id: Optional[uuid.UUID],
        user_id: uuid.UUID,
    ) -> List[BreadcrumbItem]:
        """Compute the hierarchical breadcrumb path from Root to the given folder."""
        breadcrumbs: List[BreadcrumbItem] = [
            BreadcrumbItem(id=None, name="My Drive")
        ]
        if folder_id is None:
            return breadcrumbs

        trail: List[BreadcrumbItem] = []
        current_id: Optional[uuid.UUID] = folder_id
        depth = 0
        max_depth = 50

        while current_id is not None and depth < max_depth:
            folder = db.scalars(
                select(Folder).where(Folder.id == current_id, Folder.owner_id == user_id)
            ).first()
            if not folder:
                break
            trail.append(BreadcrumbItem(id=folder.id, name=folder.name))
            current_id = folder.parent_id
            depth += 1

        trail.reverse()
        breadcrumbs.extend(trail)
        return breadcrumbs

    @staticmethod
    def is_folder_starred(db: Session, folder_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check whether a folder is starred by the user."""
        star = db.scalars(
            select(Star).where(Star.user_id == user_id, Star.folder_id == folder_id)
        ).first()
        return star is not None

    @staticmethod
    def get_starred_folder_ids(db: Session, user_id: uuid.UUID) -> Set[uuid.UUID]:
        """Fetch all starred folder UUIDs for a given user."""
        stmt = select(Star.folder_id).where(Star.user_id == user_id, Star.folder_id.is_not(None))
        return set(db.scalars(stmt).all())

    @staticmethod
    def get_starred_file_ids(db: Session, user_id: uuid.UUID) -> Set[uuid.UUID]:
        """Fetch all starred file UUIDs for a given user."""
        stmt = select(Star.file_id).where(Star.user_id == user_id, Star.file_id.is_not(None))
        return set(db.scalars(stmt).all())

    @staticmethod
    def get_folder_detail(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> FolderDetailResponse:
        """Fetch full folder details including breadcrumbs, child counts, and starred status."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=False,
        )

        breadcrumbs = FolderService.get_folder_breadcrumbs(db=db, folder_id=folder.id, user_id=user_id)

        subfolders_count = db.scalar(
            select(func.count(Folder.id)).where(
                Folder.parent_id == folder_id,
                Folder.owner_id == user_id,
                Folder.is_deleted.is_(False),
            )
        ) or 0

        files_count = db.scalar(
            select(func.count(File.id)).where(
                File.folder_id == folder_id,
                File.owner_id == user_id,
                File.is_deleted.is_(False),
            )
        ) or 0

        is_starred = FolderService.is_folder_starred(db=db, folder_id=folder_id, user_id=user_id)

        return FolderDetailResponse(
            id=folder.id,
            name=folder.name,
            parent_id=folder.parent_id,
            owner_id=folder.owner_id,
            color=folder.color,
            is_deleted=folder.is_deleted,
            deleted_at=folder.deleted_at,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            is_starred=is_starred,
            breadcrumbs=breadcrumbs,
            subfolders_count=subfolders_count,
            files_count=files_count,
        )

    @staticmethod
    def get_folder_contents(
        db: Session,
        user_id: uuid.UUID,
        folder_id: Optional[uuid.UUID] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> FolderContentsResponse:
        """List active child subfolders and files for a directory or Root."""
        current_folder_resp: Optional[FolderResponse] = None
        if folder_id is not None:
            folder = FolderService.get_folder_by_id(
                db=db,
                folder_id=folder_id,
                user_id=user_id,
                include_deleted=False,
            )
            is_starred = FolderService.is_folder_starred(db=db, folder_id=folder.id, user_id=user_id)
            current_folder_resp = FolderResponse(
                id=folder.id,
                name=folder.name,
                parent_id=folder.parent_id,
                owner_id=folder.owner_id,
                color=folder.color,
                is_deleted=folder.is_deleted,
                deleted_at=folder.deleted_at,
                created_at=folder.created_at,
                updated_at=folder.updated_at,
                is_starred=is_starred,
            )

        breadcrumbs = FolderService.get_folder_breadcrumbs(db=db, folder_id=folder_id, user_id=user_id)
        starred_folder_ids = FolderService.get_starred_folder_ids(db=db, user_id=user_id)
        starred_file_ids = FolderService.get_starred_file_ids(db=db, user_id=user_id)

        # 1. Fetch subfolders
        folders_query = select(Folder).where(
            Folder.owner_id == user_id,
            Folder.parent_id == folder_id,
            Folder.is_deleted.is_(False),
        )
        if sort_by == "created_at":
            folders_query = folders_query.order_by(
                Folder.created_at.desc() if sort_order == "desc" else Folder.created_at.asc()
            )
        elif sort_by == "updated_at":
            folders_query = folders_query.order_by(
                Folder.updated_at.desc() if sort_order == "desc" else Folder.updated_at.asc()
            )
        else:
            folders_query = folders_query.order_by(
                func.lower(Folder.name).desc() if sort_order == "desc" else func.lower(Folder.name).asc()
            )

        subfolders = db.scalars(folders_query).all()

        folder_responses: List[FolderResponse] = [
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
                is_starred=(f.id in starred_folder_ids),
            )
            for f in subfolders
        ]

        # 2. Fetch files
        files_query = select(File).where(
            File.owner_id == user_id,
            File.folder_id == folder_id,
            File.is_deleted.is_(False),
        )
        if sort_by == "size":
            files_query = files_query.order_by(
                File.size_bytes.desc() if sort_order == "desc" else File.size_bytes.asc()
            )
        elif sort_by == "created_at":
            files_query = files_query.order_by(
                File.created_at.desc() if sort_order == "desc" else File.created_at.asc()
            )
        elif sort_by == "updated_at":
            files_query = files_query.order_by(
                File.updated_at.desc() if sort_order == "desc" else File.updated_at.asc()
            )
        else:
            files_query = files_query.order_by(
                func.lower(File.name).desc() if sort_order == "desc" else func.lower(File.name).asc()
            )

        files = db.scalars(files_query).all()

        file_responses: List[FileResponse] = [
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
                is_starred=(fi.id in starred_file_ids),
            )
            for fi in files
        ]

        return FolderContentsResponse(
            current_folder=current_folder_resp,
            breadcrumbs=breadcrumbs,
            folders=folder_responses,
            files=file_responses,
            total_folders=len(folder_responses),
            total_files=len(file_responses),
        )

    @staticmethod
    def get_folder_tree(db: Session, user_id: uuid.UUID) -> List[FolderTreeItem]:
        """Construct a complete nested folder hierarchy tree for the user."""
        all_folders = db.scalars(
            select(Folder).where(
                Folder.owner_id == user_id,
                Folder.is_deleted.is_(False),
            ).order_by(func.lower(Folder.name).asc())
        ).all()

        # Group folders by parent_id
        children_map: Dict[Optional[uuid.UUID], List[Folder]] = {}
        for folder in all_folders:
            children_map.setdefault(folder.parent_id, []).append(folder)

        def build_branch(parent_id: Optional[uuid.UUID]) -> List[FolderTreeItem]:
            nodes: List[FolderTreeItem] = []
            for child in children_map.get(parent_id, []):
                node = FolderTreeItem(
                    id=child.id,
                    name=child.name,
                    parent_id=child.parent_id,
                    color=child.color,
                    children=build_branch(child.id),
                )
                nodes.append(node)
            return nodes

        return build_branch(None)

    @staticmethod
    def update_folder(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
        update_in: FolderUpdate,
        ip_address: Optional[str] = None,
    ) -> Folder:
        """Update folder attributes (rename or change color tag)."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=False,
        )

        old_name = folder.name
        details: Dict[str, Any] = {}

        if update_in.name is not None and update_in.name != folder.name:
            # Check duplicate name among siblings
            dup_query = select(Folder).where(
                Folder.owner_id == user_id,
                Folder.parent_id == folder.parent_id,
                Folder.id != folder.id,
                Folder.is_deleted.is_(False),
                func.lower(Folder.name) == update_in.name.lower(),
            )
            if db.scalars(dup_query).first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A folder named '{update_in.name}' already exists in this location.",
                )
            details["old_name"] = old_name
            details["new_name"] = update_in.name
            folder.name = update_in.name

        if update_in.color is not None:
            details["old_color"] = folder.color
            details["new_color"] = update_in.color
            folder.color = update_in.color

        if details:
            ActivityService.log_activity(
                db=db,
                action="FOLDER_UPDATE",
                resource_type="FOLDER",
                resource_id=folder.id,
                user_id=user_id,
                details=details,
                ip_address=ip_address,
            )

        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def move_folder(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
        destination_parent_id: Optional[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> Folder:
        """Move a folder to a new destination folder with cycle loop prevention."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=False,
        )

        # 1. Prevent moving into self
        if destination_parent_id == folder.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move a folder into itself.",
            )

        # 2. If moving to same parent, no-op
        if destination_parent_id == folder.parent_id:
            return folder

        # 3. If destination is specified, validate destination and prevent circular nesting
        if destination_parent_id is not None:
            dest_folder = FolderService.get_folder_by_id(
                db=db,
                folder_id=destination_parent_id,
                user_id=user_id,
                include_deleted=False,
            )
            if dest_folder.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Destination folder not found.",
                )

            # Check if destination is a descendant of the source folder
            current_ancestor_id: Optional[uuid.UUID] = dest_folder.parent_id
            depth = 0
            while current_ancestor_id is not None and depth < 50:
                if current_ancestor_id == folder.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot move a folder into one of its own subdirectories.",
                    )
                ancestor = db.scalars(
                    select(Folder).where(Folder.id == current_ancestor_id, Folder.owner_id == user_id)
                ).first()
                if not ancestor:
                    break
                current_ancestor_id = ancestor.parent_id
                depth += 1

        # 4. Check for name collision in destination
        dup_query = select(Folder).where(
            Folder.owner_id == user_id,
            Folder.parent_id == destination_parent_id,
            Folder.id != folder.id,
            Folder.is_deleted.is_(False),
            func.lower(Folder.name) == folder.name.lower(),
        )
        if db.scalars(dup_query).first():
            dest_name = "Root" if destination_parent_id is None else "the destination folder"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A folder named '{folder.name}' already exists in {dest_name}.",
            )

        old_parent_id = folder.parent_id
        folder.parent_id = destination_parent_id

        ActivityService.log_activity(
            db=db,
            action="FOLDER_MOVE",
            resource_type="FOLDER",
            resource_id=folder.id,
            user_id=user_id,
            details={
                "name": folder.name,
                "old_parent_id": str(old_parent_id) if old_parent_id else None,
                "new_parent_id": str(destination_parent_id) if destination_parent_id else None,
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def _get_all_descendant_folder_ids(
        db: Session,
        root_folder_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[uuid.UUID]:
        """Collect all descendant folder UUIDs using iterative BFS traversal."""
        descendants: List[uuid.UUID] = []
        queue: List[uuid.UUID] = [root_folder_id]

        while queue:
            current_id = queue.pop(0)
            child_ids = db.scalars(
                select(Folder.id).where(
                    Folder.parent_id == current_id,
                    Folder.owner_id == user_id,
                )
            ).all()
            for cid in child_ids:
                descendants.append(cid)
                queue.append(cid)

        return descendants

    @staticmethod
    def soft_delete_folder(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Folder:
        """Recursively soft-delete a folder and all its descendant subfolders and files."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=False,
        )

        now = datetime.now(timezone.utc)
        descendant_ids = FolderService._get_all_descendant_folder_ids(db, folder.id, user_id)
        all_target_folder_ids = [folder.id] + descendant_ids

        # Mark folder and subfolders as deleted
        for fid in all_target_folder_ids:
            f = db.scalars(select(Folder).where(Folder.id == fid)).first()
            if f and not f.is_deleted:
                f.is_deleted = True
                f.deleted_at = now

        # Mark all files in these folders as deleted
        files = db.scalars(
            select(File).where(
                File.folder_id.in_(all_target_folder_ids),
                File.owner_id == user_id,
                File.is_deleted.is_(False),
            )
        ).all()
        for fi in files:
            fi.is_deleted = True
            fi.deleted_at = now

        ActivityService.log_activity(
            db=db,
            action="FOLDER_DELETE",
            resource_type="FOLDER",
            resource_id=folder.id,
            user_id=user_id,
            details={
                "name": folder.name,
                "cascade_folders_count": len(descendant_ids),
                "cascade_files_count": len(files),
            },
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def restore_folder(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Folder:
        """Recursively restore a soft-deleted folder and its descendant items from the Trash."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=True,
        )

        if not folder.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder is not in the Trash.",
            )

        # If parent folder is also deleted or nonexistent, restore this folder directly to Root
        if folder.parent_id is not None:
            parent = db.scalars(
                select(Folder).where(Folder.id == folder.parent_id, Folder.owner_id == user_id)
            ).first()
            if not parent or parent.is_deleted:
                folder.parent_id = None

        # Check duplicate name collision in target destination
        dup_query = select(Folder).where(
            Folder.owner_id == user_id,
            Folder.parent_id == folder.parent_id,
            Folder.id != folder.id,
            Folder.is_deleted.is_(False),
            func.lower(Folder.name) == folder.name.lower(),
        )
        if db.scalars(dup_query).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot restore: a folder named '{folder.name}' already exists in this location.",
            )

        descendant_ids = FolderService._get_all_descendant_folder_ids(db, folder.id, user_id)
        all_target_folder_ids = [folder.id] + descendant_ids

        # Restore folders
        for fid in all_target_folder_ids:
            f = db.scalars(select(Folder).where(Folder.id == fid)).first()
            if f and f.is_deleted:
                f.is_deleted = False
                f.deleted_at = None

        # Restore files
        files = db.scalars(
            select(File).where(
                File.folder_id.in_(all_target_folder_ids),
                File.owner_id == user_id,
                File.is_deleted.is_(True),
            )
        ).all()
        for fi in files:
            fi.is_deleted = False
            fi.deleted_at = None

        ActivityService.log_activity(
            db=db,
            action="FOLDER_RESTORE",
            resource_type="FOLDER",
            resource_id=folder.id,
            user_id=user_id,
            details={"name": folder.name},
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def hard_delete_folder(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Permanently delete a folder and all cascading records from the database."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=True,
        )

        descendant_ids = FolderService._get_all_descendant_folder_ids(db, folder.id, user_id)
        # Delete from leaf to root to respect foreign key restrictions
        all_target_folder_ids = list(reversed(descendant_ids)) + [folder.id]

        for fid in all_target_folder_ids:
            f = db.scalars(select(Folder).where(Folder.id == fid)).first()
            if f:
                # Delete files inside the folder first
                child_files = db.scalars(select(File).where(File.folder_id == fid)).all()
                for cfile in child_files:
                    db.delete(cfile)
                db.delete(f)

        ActivityService.log_activity(
            db=db,
            action="FOLDER_PURGE",
            resource_type="FOLDER",
            resource_id=folder_id,
            user_id=user_id,
            details={"name": folder.name},
            ip_address=ip_address,
        )

        db.commit()

    @staticmethod
    def toggle_star(
        db: Session,
        folder_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Toggle star/favorite status for a folder. Returns True if starred, False if unstarred."""
        folder = FolderService.get_folder_by_id(
            db=db,
            folder_id=folder_id,
            user_id=user_id,
            include_deleted=False,
        )

        existing_star = db.scalars(
            select(Star).where(Star.user_id == user_id, Star.folder_id == folder.id)
        ).first()

        if existing_star:
            db.delete(existing_star)
            ActivityService.log_activity(
                db=db,
                action="FOLDER_UNSTAR",
                resource_type="FOLDER",
                resource_id=folder.id,
                user_id=user_id,
                details={"name": folder.name},
            )
            db.commit()
            return False
        else:
            star = Star(user_id=user_id, folder_id=folder.id)
            db.add(star)
            ActivityService.log_activity(
                db=db,
                action="FOLDER_STAR",
                resource_type="FOLDER",
                resource_id=folder.id,
                user_id=user_id,
                details={"name": folder.name},
            )
            db.commit()
            return True
