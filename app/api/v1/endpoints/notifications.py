"""Notification endpoints for retrieving user alerts and updating read status."""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.notification import NotificationOut, NotificationSummary
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/me", response_model=StandardResponse[NotificationSummary])
async def get_my_notifications(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recent notifications and unread count for current user."""
    service = NotificationService(db)
    summary = await service.list_user_notifications(current_user.id, limit=limit)
    return StandardResponse(
        success=True,
        message="Notifications retrieved",
        data=summary,
    )


@router.patch("/{notification_id}/read", response_model=StandardResponse[NotificationOut])
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    service = NotificationService(db)
    notification = await service.mark_as_read(notification_id, current_user.id)
    return StandardResponse(
        success=True,
        message="Notification marked as read",
        data=NotificationOut.model_validate(notification),
    )


@router.post("/read-all", response_model=StandardResponse[dict])
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all unread notifications as read for current user."""
    service = NotificationService(db)
    updated_count = await service.mark_all_as_read(current_user.id)
    return StandardResponse(
        success=True,
        message=f"{updated_count} notification(s) marked as read",
        data={"updated_count": updated_count},
    )
