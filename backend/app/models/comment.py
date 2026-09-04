import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File

class Comment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """File collaboration comment created by file owners or shared users."""

    __tablename__ = "comments"

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target file UUID.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Author user UUID.",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Markdown or plain text comment content.",
    )

    file: Mapped["File"] = relationship("File", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, file_id={self.file_id}, user_id={self.user_id})>"
