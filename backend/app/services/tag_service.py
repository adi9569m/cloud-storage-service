from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.folder import Folder
from app.models.tag import ItemTag, Tag
from app.schemas.tag import (
    TagAttachRequest,
    TagCreate,
    TagDetachRequest,
    TaggedItemsResponse,
    TagResponse,
    TagUpdate,
)
from app.services.file_service import FileService
from app.services.folder_service import FolderService

class TagService:
    """Service handling CRUD and item labeling operations for custom tags."""

    @classmethod
    def to_tag_response(cls, db: Session, tag: Tag) -> TagResponse:
        """Convert Tag model to TagResponse schema with computed item count."""
        count = db.scalar(
            select(func.count(ItemTag.id)).where(ItemTag.tag_id == tag.id)
        ) or 0

        return TagResponse(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            user_id=tag.user_id,
            item_count=count,
            created_at=tag.created_at,
            updated_at=tag.updated_at,
        )

    @classmethod
    def create_tag(cls, db: Session, user_id: uuid.UUID, tag_in: TagCreate) -> TagResponse:
        """Create a new custom tag for the user."""
        clean_name = tag_in.name.strip()
        existing = db.scalars(
            select(Tag).where(Tag.user_id == user_id, func.lower(Tag.name) == clean_name.lower())
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A tag named '{clean_name}' already exists.",
            )

        tag = Tag(
            name=clean_name,
            color=tag_in.color.strip() if tag_in.color else "#3B82F6",
            user_id=user_id,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return cls.to_tag_response(db, tag)

    @classmethod
    def list_user_tags(cls, db: Session, user_id: uuid.UUID) -> List[TagResponse]:
        """List all custom tags created by user."""
        tags = db.scalars(
            select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
        ).all()
        return [cls.to_tag_response(db, t) for t in tags]

    @classmethod
    def get_tag_by_id(cls, db: Session, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag:
        """Fetch a tag ensuring ownership."""
        tag = db.scalars(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        ).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found.",
            )
        return tag

    @classmethod
    def update_tag(cls, db: Session, tag_id: uuid.UUID, user_id: uuid.UUID, tag_in: TagUpdate) -> TagResponse:
        """Update tag name or accent color."""
        tag = cls.get_tag_by_id(db=db, tag_id=tag_id, user_id=user_id)

        if tag_in.name is not None:
            clean_name = tag_in.name.strip()
            duplicate = db.scalars(
                select(Tag).where(
                    Tag.user_id == user_id,
                    Tag.id != tag.id,
                    func.lower(Tag.name) == clean_name.lower(),
                )
            ).first()
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A tag named '{clean_name}' already exists.",
                )
            tag.name = clean_name

        if tag_in.color is not None:
            tag.color = tag_in.color.strip()

        db.commit()
        db.refresh(tag)
        return cls.to_tag_response(db, tag)

    @classmethod
    def delete_tag(cls, db: Session, tag_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a tag and automatically clear its item associations."""
        tag = cls.get_tag_by_id(db=db, tag_id=tag_id, user_id=user_id)
        db.delete(tag)
        db.commit()

    @classmethod
    def attach_tag(cls, db: Session, user_id: uuid.UUID, attach_in: TagAttachRequest) -> None:
        """Attach a tag to a target file or folder."""
        tag = cls.get_tag_by_id(db=db, tag_id=attach_in.tag_id, user_id=user_id)

        if attach_in.file_id is None and attach_in.folder_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify either file_id or folder_id to attach tag.",
            )
        if attach_in.file_id is not None and attach_in.folder_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot specify both file_id and folder_id in a single attach request.",
            )

        if attach_in.file_id is not None:

            FileService.get_file_by_id(db=db, file_id=attach_in.file_id, user_id=user_id, include_deleted=False)
            existing = db.scalars(
                select(ItemTag).where(ItemTag.tag_id == tag.id, ItemTag.file_id == attach_in.file_id)
            ).first()
            if not existing:
                db.add(ItemTag(tag_id=tag.id, file_id=attach_in.file_id))

        if attach_in.folder_id is not None:

            FolderService.get_folder_by_id(db=db, folder_id=attach_in.folder_id, user_id=user_id, include_deleted=False)
            existing = db.scalars(
                select(ItemTag).where(ItemTag.tag_id == tag.id, ItemTag.folder_id == attach_in.folder_id)
            ).first()
            if not existing:
                db.add(ItemTag(tag_id=tag.id, folder_id=attach_in.folder_id))

        db.commit()

    @classmethod
    def detach_tag(cls, db: Session, user_id: uuid.UUID, detach_in: TagDetachRequest) -> None:
        """Detach a tag from a target file or folder."""
        tag = cls.get_tag_by_id(db=db, tag_id=detach_in.tag_id, user_id=user_id)

        if detach_in.file_id is not None:
            item_tag = db.scalars(
                select(ItemTag).where(ItemTag.tag_id == tag.id, ItemTag.file_id == detach_in.file_id)
            ).first()
            if item_tag:
                db.delete(item_tag)

        if detach_in.folder_id is not None:
            item_tag = db.scalars(
                select(ItemTag).where(ItemTag.tag_id == tag.id, ItemTag.folder_id == detach_in.folder_id)
            ).first()
            if item_tag:
                db.delete(item_tag)

        db.commit()

    @classmethod
    def get_tagged_items(cls, db: Session, tag_id: uuid.UUID, user_id: uuid.UUID) -> TaggedItemsResponse:
        """Fetch all active files and folders labeled with a specific tag."""
        tag = cls.get_tag_by_id(db=db, tag_id=tag_id, user_id=user_id)

        file_ids = db.scalars(
            select(ItemTag.file_id).where(ItemTag.tag_id == tag.id, ItemTag.file_id.is_not(None))
        ).all()

        folder_ids = db.scalars(
            select(ItemTag.folder_id).where(ItemTag.tag_id == tag.id, ItemTag.folder_id.is_not(None))
        ).all()

        files = (
            db.scalars(
                select(File).where(
                    File.id.in_(file_ids),
                    File.owner_id == user_id,
                    File.is_deleted.is_(False),
                )
            ).all()
            if file_ids
            else []
        )

        folders = (
            db.scalars(
                select(Folder).where(
                    Folder.id.in_(folder_ids),
                    Folder.owner_id == user_id,
                    Folder.is_deleted.is_(False),
                )
            ).all()
            if folder_ids
            else []
        )

        file_responses = [FileService.to_file_response(db, f, user_id) for f in files]
        folder_responses = [
            FolderService.get_folder_detail(db, f.id, user_id)
            for f in folders
        ]

        return TaggedItemsResponse(
            tag=cls.to_tag_response(db, tag),
            files=file_responses,
            folders=folder_responses,
        )

    @classmethod
    def list_tags_for_item(
        cls,
        db: Session,
        user_id: uuid.UUID,
        file_id: Optional[uuid.UUID] = None,
        folder_id: Optional[uuid.UUID] = None,
    ) -> List[TagResponse]:
        """Fetch all tags applied to a specific file or folder."""
        query = select(Tag).join(ItemTag, ItemTag.tag_id == Tag.id).where(Tag.user_id == user_id)
        if file_id is not None:
            query = query.where(ItemTag.file_id == file_id)
        elif folder_id is not None:
            query = query.where(ItemTag.folder_id == folder_id)
        else:
            return []

        tags = db.scalars(query).all()
        return [cls.to_tag_response(db, t) for t in tags]
