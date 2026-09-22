"""Notification service for dispatching, listing, and marking user notifications."""

from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import NotificationChannel
from app.core.exceptions import ResourceNotFoundError
from app.models.emergency import Notification
from app.schemas.notification import NotificationOut, NotificationSummary


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        recipient_id: uuid.UUID,
        title: str,
        body: str,
        data: Optional[dict] = None,
        channel: NotificationChannel = NotificationChannel.IN_APP,
    ) -> Notification:
        """Persist a new notification for a recipient user."""
        notification = Notification(
            recipient_id=recipient_id,
            title=title,
            body=body,
            channel=channel,
            is_read=False,
            data=data or {},
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def list_user_notifications(
        self, user_id: uuid.UUID, limit: int = 30
    ) -> NotificationSummary:
        """Retrieve recent notifications and unread count for the user."""
        # 1. Count unread
        unread_count_query = (
            select(func.count(Notification.id))
            .where(
                Notification.recipient_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        unread_count = (await self.db.execute(unread_count_query)).scalar_one() or 0

        # 2. Fetch recent notifications
        query = (
            select(Notification)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return NotificationSummary(
            unread_count=unread_count,
            items=[NotificationOut.model_validate(n) for n in items],
        )

    async def mark_as_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification:
        """Mark a specific notification as read."""
        query = select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == user_id,
        ).with_for_update()
        notification = (await self.db.execute(query)).scalar_one_or_none()
        if not notification:
            raise ResourceNotFoundError(message="Notification not found")

        notification.is_read = True
        await self.db.flush()
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications as read for a user."""
        stmt = (
            update(Notification)
            .where(
                Notification.recipient_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount
