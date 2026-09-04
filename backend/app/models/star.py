import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.folder import Folder

class Star(Base, UUIDPrimaryKeyMixin):
    """User star/favorite bookmark entity for quick resource access."""

    __tablename__ = "stars"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID of the user who starred the resource.",
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
        doc="Starred file ID.",
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
        doc="Starred folder ID.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the item was starred (UTC).",
    )

    __table_args__ = (
        CheckConstraint(
            "(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)",
            name="chk_stars_target",
        ),
        Index("idx_stars_user_file", "user_id", "file_id"),
        Index("idx_stars_user_folder", "user_id", "folder_id"),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="stars",
        foreign_keys=[user_id],
    )
    file: Mapped["File | None"] = relationship(
        "File",
        back_populates="stars",
        foreign_keys=[file_id],
    )
    folder: Mapped["Folder | None"] = relationship(
        "Folder",
        back_populates="stars",
        foreign_keys=[folder_id],
    )

    def __repr__(self) -> str:
        return f"<Star(id={self.id}, user_id={self.user_id}, file_id={self.file_id}, folder_id={self.folder_id})>"
