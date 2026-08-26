"""User SQLAlchemy ORM model representing platform users."""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.folder import Folder
    from app.models.file import File
    from app.models.file_version import FileVersion
    from app.models.share import Share
    from app.models.link_share import LinkShare
    from app.models.star import Star
    from app.models.activity import Activity


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User account entity for authentication, ownership, and permissions."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique user email address.",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Securely hashed password (bcrypt).",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        default=None,
        doc="Full display name of the user.",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
        doc="Profile avatar image URL.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active.",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user email is verified.",
    )
    storage_used_bytes: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
        doc="Aggregated storage consumption in bytes.",
    )

    # Relationships
    folders: Mapped[List["Folder"]] = relationship(
        "Folder",
        back_populates="owner",
        foreign_keys="Folder.owner_id",
    )
    files: Mapped[List["File"]] = relationship(
        "File",
        back_populates="owner",
        foreign_keys="File.owner_id",
    )
    uploaded_versions: Mapped[List["FileVersion"]] = relationship(
        "FileVersion",
        back_populates="uploaded_by",
        foreign_keys="FileVersion.uploaded_by_id",
    )
    shares_granted: Mapped[List["Share"]] = relationship(
        "Share",
        back_populates="granter",
        foreign_keys="Share.granter_id",
    )
    shares_received: Mapped[List["Share"]] = relationship(
        "Share",
        back_populates="grantee",
        foreign_keys="Share.grantee_id",
    )
    link_shares: Mapped[List["LinkShare"]] = relationship(
        "LinkShare",
        back_populates="created_by",
        foreign_keys="LinkShare.created_by_id",
    )
    stars: Mapped[List["Star"]] = relationship(
        "Star",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"
