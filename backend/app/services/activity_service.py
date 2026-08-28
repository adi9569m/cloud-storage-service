"""Service handling audit trail and system activity logging."""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.activity import Activity


class ActivityService:
    """Provides methods to record audit logs for resource actions."""

    @staticmethod
    def log_activity(
        db: Session,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> Activity:
        """Create and persist an activity audit record."""
        activity = Activity(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        db.add(activity)
        # Note: We don't commit here immediately so that activity logging participates in the caller transaction
        return activity
