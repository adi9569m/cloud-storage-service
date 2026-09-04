import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from app.models.share import ShareRole

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.folder import Folder

class LinkShare(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Public token-based share link with optional expiry and password protection."""

    __tablename__ = "link_shares"

    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="Secure URL-safe random access token.",
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User ID of the link creator.",
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
        doc="Target file ID (if sharing a file).",
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
        doc="Target folder ID (if sharing a folder).",
    )
    role: Mapped[ShareRole] = mapped_column(
        Enum(ShareRole, name="link_share_role_enum", native_enum=False, length=20),
        nullable=False,
        default=ShareRole.VIEWER,
        doc="Permitted permission role for public link consumers.",
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        doc="Bcrypt hash for password-protected links. Null if public/unrestricted.",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Expiration timestamp (UTC). Null if link does not expire.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Toggle flag to enable or deactivate the link immediately.",
    )
    access_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of visits / accesses via this link.",
    )

    __table_args__ = (
        CheckConstraint(
            "(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)",
            name="chk_link_shares_target",
        ),
        Index("idx_link_shares_token", "token"),
        Index("idx_link_shares_file", "file_id"),
        Index("idx_link_shares_folder", "folder_id"),
    )

    created_by: Mapped["User"] = relationship(
        "User",
        back_populates="link_shares",
        foreign_keys=[created_by_id],
    )
    file: Mapped["File | None"] = relationship(
        "File",
        back_populates="link_shares",
        foreign_keys=[file_id],
    )
    folder: Mapped["Folder | None"] = relationship(
        "Folder",
        back_populates="link_shares",
        foreign_keys=[folder_id],
    )

    def __repr__(self) -> str:
        return f"<LinkShare(id={self.id}, token='{self.token[:8]}...', role='{self.role.value}', is_active={self.is_active})>"
