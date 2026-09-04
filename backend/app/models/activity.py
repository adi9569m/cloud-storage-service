import uuid
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

class Activity(Base, UUIDPrimaryKeyMixin):
    """Audit log tracking system events, uploads, deletions, shares, and updates."""

    __tablename__ = "activities"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
        doc="User ID who triggered the action. Null for system actions or removed accounts.",
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Action identifier (e.g. FILE_UPLOAD, FILE_DELETE, FOLDER_CREATE, SHARE_GRANTED).",
    )
    resource_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Entity type affected: FILE, FOLDER, SHARE, LINK_SHARE.",
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
        doc="Target entity UUID.",
    )
    details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        doc="Structured event payload (e.g. filename, old_name, new_name, recipient).",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,
        doc="Client IP address for security logging.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when the activity occurred (UTC).",
    )

    __table_args__ = (
        Index("idx_activities_resource", "resource_type", "resource_id"),
        Index("idx_activities_user_created", "user_id", "created_at"),
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="activities",
        foreign_keys=[user_id],
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"
