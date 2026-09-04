import enum
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.folder import Folder

class ShareRole(str, enum.Enum):
    """Permitted access roles for shared resources."""

    VIEWER = "VIEWER"
    EDITOR = "EDITOR"

class Share(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Direct user-to-user share permission record with role-based access control."""

    __tablename__ = "shares"

    granter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User ID of the user granting the share.",
    )
    grantee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID of the recipient user receiving access.",
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
        Enum(ShareRole, name="share_role_enum", native_enum=False, length=20),
        nullable=False,
        default=ShareRole.VIEWER,
        doc="Assigned role: VIEWER (read-only) or EDITOR (read/write).",
    )

    __table_args__ = (
        CheckConstraint(
            "(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)",
            name="chk_shares_target",
        ),
        Index("idx_shares_grantee_file", "grantee_id", "file_id"),
        Index("idx_shares_grantee_folder", "grantee_id", "folder_id"),
    )

    granter: Mapped["User"] = relationship(
        "User",
        back_populates="shares_granted",
        foreign_keys=[granter_id],
    )
    grantee: Mapped["User"] = relationship(
        "User",
        back_populates="shares_received",
        foreign_keys=[grantee_id],
    )
    file: Mapped["File | None"] = relationship(
        "File",
        back_populates="shares",
        foreign_keys=[file_id],
    )
    folder: Mapped["Folder | None"] = relationship(
        "Folder",
        back_populates="shares",
        foreign_keys=[folder_id],
    )

    def __repr__(self) -> str:
        return f"<Share(id={self.id}, grantee_id={self.grantee_id}, role='{self.role.value}')>"
