import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class BreadcrumbItem(BaseModel):
    """Breadcrumb trail entry representing hierarchical folder navigation."""

    id: Optional[uuid.UUID] = Field(None, description="Folder UUID. None indicates Root.")
    name: str = Field(..., description="Folder display name or 'My Drive' for Root.")

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    """Standard message response envelope."""

    message: str = Field(..., description="Human-readable response message")
    detail: Optional[str] = Field(None, description="Optional extra details")

class ErrorResponse(BaseModel):
    """Standardized error envelope as defined by architecture specification."""

    detail: str = Field(..., description="Descriptive error message")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
