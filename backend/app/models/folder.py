"""Folder SQLAlchemy ORM model representing nested directory hierarchy."""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.share import Share
    from app.models.link_share import LinkShare
    from app.models.star import Star


class Folder(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Folder entity supporting multi-level nesting and soft deletion."""

    __tablename__ = "folders"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Folder display name.",
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("folders.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
        doc="Parent folder ID. Null for top-level root folders.",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User ID of the folder owner.",
    )
    color: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
        doc="UI color tag for the folder.",
    )

    # Table arguments / composite indexes
    __table_args__ = (
        Index("idx_folders_owner_parent", "owner_id", "parent_id", "is_deleted"),
        Index("idx_folders_is_deleted", "is_deleted", "deleted_at"),
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="folders",
        foreign_keys=[owner_id],
    )
    parent: Mapped["Folder | None"] = relationship(
        "Folder",
        remote_side="Folder.id",
        back_populates="subfolders",
        foreign_keys=[parent_id],
    )
    subfolders: Mapped[List["Folder"]] = relationship(
        "Folder",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    files: Mapped[List["File"]] = relationship(
        "File",
        back_populates="folder",
        foreign_keys="File.folder_id",
    )
    shares: Mapped[List["Share"]] = relationship(
        "Share",
        back_populates="folder",
        cascade="all, delete-orphan",
        foreign_keys="Share.folder_id",
    )
    link_shares: Mapped[List["LinkShare"]] = relationship(
        "LinkShare",
        back_populates="folder",
        cascade="all, delete-orphan",
        foreign_keys="LinkShare.folder_id",
    )
    stars: Mapped[List["Star"]] = relationship(
        "Star",
        back_populates="folder",
        cascade="all, delete-orphan",
        foreign_keys="Star.folder_id",
    )

    def __repr__(self) -> str:
        return f"<Folder(id={self.id}, name='{self.name}', owner_id={self.owner_id}, is_deleted={self.is_deleted})>"
