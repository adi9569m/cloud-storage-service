"""Pydantic schemas for file content preview and text inspection."""

import uuid
from pydantic import BaseModel, Field


class TextContentResponse(BaseModel):
    """Raw text/code content and inspection metadata for in-browser file preview."""

    id: uuid.UUID
    name: str
    mime_type: str
    size_bytes: int
    encoding: str = "utf-8"
    content: str
    line_count: int
    is_truncated: bool = Field(False, description="True if content exceeded max preview size and was truncated")
