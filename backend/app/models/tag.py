from datetime import datetime, timezone
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.folder import Folder

class ItemTag(Base, UUIDPrimaryKeyMixin):
    """Association entity linking tags to files or folders."""

    __tablename__ = "item_tags"

    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("tag_id", "file_id", name="uq_item_tags_tag_file"),
        UniqueConstraint("tag_id", "folder_id", name="uq_item_tags_tag_folder"),
    )

class Tag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Custom color-coded tag entity created by users."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Tag display name (e.g., Work, Finance, Important).",
    )
    color: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="#3B82F6",
        doc="Hex or CSS color string for UI rendering.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user who created the tag.",
    )

    user: Mapped["User"] = relationship("User", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', color='{self.color}')>"
