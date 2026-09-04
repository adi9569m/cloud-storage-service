import uuid
from datetime import datetime
from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

class UUIDPrimaryKeyMixin:
    """Mixin that provides a UUID primary key for database entities."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Universally unique identifier for the entity.",
    )

class TimestampMixin:
    """Mixin that provides creation and update timestamps with timezone awareness."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the entity record was created (UTC).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the entity record was last updated (UTC).",
    )

class SoftDeleteMixin:
    """Mixin that provides soft delete capability for trash and restore management."""

    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        doc="Soft deletion flag. True indicates the resource is in the Trash.",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the resource was moved to Trash (UTC).",
    )
