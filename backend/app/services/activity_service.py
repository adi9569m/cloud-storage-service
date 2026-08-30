"""Service handling audit trail, system activity logging, and activity feeds."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.models.activity import Activity
from app.schemas.activity import ActivityListResponse, ActivityResponse


class ActivityService:
    """Provides methods to record and query audit logs for resource actions."""

    @staticmethod
    def _to_activity_response(activity: Activity) -> ActivityResponse:
        """Convert Activity entity to ActivityResponse schema."""
        return ActivityResponse(
            id=activity.id,
            user_id=activity.user_id,
            user_email=activity.user.email if activity.user else None,
            action=activity.action,
            resource_type=activity.resource_type,
            resource_id=activity.resource_id,
            details=activity.details,
            ip_address=activity.ip_address,
            created_at=activity.created_at,
        )

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
        return activity

    @staticmethod
    def list_user_activities(
        db: Session,
        user_id: uuid.UUID,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ActivityListResponse:
        """Retrieve paginated activity logs initiated by or involving the user."""
        query = (
            select(Activity)
            .options(joinedload(Activity.user))
            .where(Activity.user_id == user_id)
        )
        count_query = select(func.count(Activity.id)).where(Activity.user_id == user_id)

        if resource_type:
            query = query.where(Activity.resource_type == resource_type.upper())
            count_query = count_query.where(Activity.resource_type == resource_type.upper())

        if action:
            query = query.where(Activity.action == action.upper())
            count_query = count_query.where(Activity.action == action.upper())

        total_count = db.scalar(count_query) or 0

        activities = db.scalars(
            query.order_by(Activity.created_at.desc()).offset(offset).limit(limit)
        ).all()

        return ActivityListResponse(
            items=[ActivityService._to_activity_response(a) for a in activities],
            total_count=total_count,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def list_resource_activities(
        db: Session,
        user_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> ActivityListResponse:
        """Retrieve paginated audit history for a specific resource, checking permissions."""
        from app.services.share_service import ShareService

        res_type = resource_type.upper()
        if res_type == "FILE":
            has_access, _ = ShareService.check_user_access(db=db, user_id=user_id, file_id=resource_id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to file audit trail.")
        elif res_type == "FOLDER":
            has_access, _ = ShareService.check_user_access(db=db, user_id=user_id, folder_id=resource_id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to folder audit trail.")

        query = (
            select(Activity)
            .options(joinedload(Activity.user))
            .where(
                Activity.resource_type == res_type,
                Activity.resource_id == resource_id,
            )
        )
        count_query = select(func.count(Activity.id)).where(
            Activity.resource_type == res_type,
            Activity.resource_id == resource_id,
        )

        total_count = db.scalar(count_query) or 0
        activities = db.scalars(
            query.order_by(Activity.created_at.desc()).offset(offset).limit(limit)
        ).all()

        return ActivityListResponse(
            items=[ActivityService._to_activity_response(a) for a in activities],
            total_count=total_count,
            limit=limit,
            offset=offset,
        )
