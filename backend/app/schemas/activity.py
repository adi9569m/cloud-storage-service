"""Pydantic schemas for audit trail activity logs."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ActivityResponse(BaseModel):
    """Schema representing an individual activity log record."""

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: uuid.UUID
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    """Paginated list of activity log entries."""

    items: List[ActivityResponse] = Field(default_factory=list)
    total_count: int = 0
    limit: int = 50
    offset: int = 0
