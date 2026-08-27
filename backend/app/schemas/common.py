"""Common reusable schemas and response models."""

from typing import Optional
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Standard message response envelope."""

    message: str = Field(..., description="Human-readable response message")
    detail: Optional[str] = Field(None, description="Optional extra details")


class ErrorResponse(BaseModel):
    """Standardized error envelope as defined by architecture specification."""

    detail: str = Field(..., description="Descriptive error message")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
