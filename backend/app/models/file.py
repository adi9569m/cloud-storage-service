"""File SQLAlchemy ORM model representing stored file objects and metadata."""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.folder import Folder
    from app.models.file_version import FileVersion
    from app.models.share import Share
    from app.models.link_share import LinkShare
    from app.models.star import Star


class File(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """File entity holding metadata, storage references, and version history."""

    __tablename__ = "files"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="File name including extension (e.g. quarterly_report.pdf).",
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
        doc="Parent folder ID. Null indicates the root storage directory.",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User ID of the file owner.",
    )
    mime_type: Mapped[str] = mapped_column(
        String(127),
        nullable=False,
        index=True,
        doc="MIME type of the current active version (e.g. application/pdf, image/jpeg).",
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
        doc="File size in bytes for the active version.",
    )
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Object storage path / key in Supabase Storage bucket.",
    )

    # Table arguments / composite indexes
    __table_args__ = (
        Index("idx_files_owner_folder", "owner_id", "folder_id", "is_deleted"),
        Index("idx_files_is_deleted", "is_deleted", "deleted_at"),
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="files",
        foreign_keys=[owner_id],
    )
    folder: Mapped["Folder | None"] = relationship(
        "Folder",
        back_populates="files",
        foreign_keys=[folder_id],
    )
    versions: Mapped[List["FileVersion"]] = relationship(
        "FileVersion",
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="desc(FileVersion.version_number)",
        foreign_keys="FileVersion.file_id",
    )
    shares: Mapped[List["Share"]] = relationship(
        "Share",
        back_populates="file",
        cascade="all, delete-orphan",
        foreign_keys="Share.file_id",
    )
    link_shares: Mapped[List["LinkShare"]] = relationship(
        "LinkShare",
        back_populates="file",
        cascade="all, delete-orphan",
        foreign_keys="LinkShare.file_id",
    )
    stars: Mapped[List["Star"]] = relationship(
        "Star",
        back_populates="file",
        cascade="all, delete-orphan",
        foreign_keys="Star.file_id",
    )

    def __repr__(self) -> str:
        return f"<File(id={self.id}, name='{self.name}', size={self.size_bytes}, owner_id={self.owner_id})>"
