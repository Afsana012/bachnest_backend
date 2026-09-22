"""Notification Pydantic schemas for BachNest."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import Field

from app.core.constants import NotificationChannel
from app.schemas.common import BaseSchema


class NotificationOut(BaseSchema):
    id: uuid.UUID
    recipient_id: uuid.UUID
    title: str
    body: str
    channel: NotificationChannel
    is_read: bool
    data: Optional[dict] = None
    created_at: datetime


class NotificationSummary(BaseSchema):
    unread_count: int = Field(default=0, ge=0)
    items: List[NotificationOut] = Field(default_factory=list)
