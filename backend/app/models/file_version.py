"""FileVersion SQLAlchemy ORM model representing historic and current file versions."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User


class FileVersion(Base, UUIDPrimaryKeyMixin):
    """Immutable version snapshot tracking binary object uploads and checksums."""

    __tablename__ = "file_versions"

    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent file ID.",
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Incremental version number for the file (1, 2, 3...).",
    )
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Unique object storage path for this specific version in Supabase Storage.",
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Size in bytes for this specific version.",
    )
    mime_type: Mapped[str] = mapped_column(
        String(127),
        nullable=False,
        doc="MIME type for this specific version.",
    )
    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
        doc="SHA-256 integrity checksum of the uploaded file binary.",
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User ID of the user who uploaded this version.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when this version was created (UTC).",
    )

    # Unique constraint and composite indexes
    __table_args__ = (
        UniqueConstraint("file_id", "version_number", name="uq_file_versions_file_version"),
        Index("idx_file_versions_file_ver", "file_id", "version_number"),
    )

    # Relationships
    file: Mapped["File"] = relationship(
        "File",
        back_populates="versions",
        foreign_keys=[file_id],
    )
    uploaded_by: Mapped["User"] = relationship(
        "User",
        back_populates="uploaded_versions",
        foreign_keys=[uploaded_by_id],
    )

    def __repr__(self) -> str:
        return f"<FileVersion(id={self.id}, file_id={self.file_id}, version={self.version_number})>"
