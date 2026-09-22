"""Unit tests for user notifications and booking message triggers."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.core.constants import NotificationChannel
from app.models.emergency import Notification
from app.schemas.notification import NotificationOut, NotificationSummary
from app.services.notification_service import NotificationService


def test_notification_out_schema():
    notif_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    schema = NotificationOut(
        id=notif_id,
        recipient_id=user_id,
        title="New message from Landlord",
        body="Landlord: okay come and visit",
        channel=NotificationChannel.IN_APP,
        is_read=False,
        data={"booking_id": "test-booking-id", "type": "BOOKING_MESSAGE"},
        created_at=now,
    )
    assert schema.id == notif_id
    assert schema.recipient_id == user_id
    assert schema.title == "New message from Landlord"
    assert schema.is_read is False
    assert schema.data["type"] == "BOOKING_MESSAGE"


def test_notification_summary_schema():
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    item = NotificationOut(
        id=uuid.uuid4(),
        recipient_id=user_id,
        title="Visit Confirmed",
        body="Landlord confirmed your inspection visit.",
        channel=NotificationChannel.IN_APP,
        is_read=False,
        data={"type": "VISIT_CONFIRMED"},
        created_at=now,
    )
    summary = NotificationSummary(unread_count=1, items=[item])
    assert summary.unread_count == 1
    assert len(summary.items) == 1
    assert summary.items[0].title == "Visit Confirmed"


@pytest.mark.asyncio
async def test_notification_service_create_notification():
    db = AsyncMock()
    service = NotificationService(db)
    user_id = uuid.uuid4()

    notif = await service.create_notification(
        recipient_id=user_id,
        title="New Message",
        body="Hello from landlord",
        data={"type": "BOOKING_MESSAGE"},
    )

    assert notif.recipient_id == user_id
    assert notif.title == "New Message"
    assert notif.is_read is False
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_notification_service_mark_as_read():
    db = AsyncMock()
    user_id = uuid.uuid4()
    notif_id = uuid.uuid4()

    mock_notif = MagicMock(spec=Notification)
    mock_notif.id = notif_id
    mock_notif.recipient_id = user_id
    mock_notif.is_read = False

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_notif
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    service = NotificationService(db)
    updated = await service.mark_as_read(notif_id, user_id)

    assert updated.is_read is True
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_notification_service_mark_all_as_read():
    db = AsyncMock()
    user_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.rowcount = 4
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    service = NotificationService(db)
    count = await service.mark_all_as_read(user_id)

    assert count == 4
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_append_message_triggers_notification_to_counterparty():
    """Verify that append_message invokes notification_service.create_notification."""
    from app.services.booking_service import BookingService

    db = AsyncMock()
    service = BookingService(db)

    # Mock notification_service
    service.notification_service = AsyncMock()

    # Mock booking
    tenant_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    mock_booking = MagicMock()
    mock_booking.id = booking_id
    mock_booking.tenant_id = tenant_id
    mock_booking.visit_notes = None
    mock_booking.property = MagicMock()
    mock_booking.property.owner_id = owner_id
    mock_booking.property.title = "Dhanmondi Master Bed"

    # User is Landlord (owner)
    landlord_user = MagicMock()
    landlord_user.id = owner_id
    landlord_user.full_name = "Bachnest Landlord"

    service.get_booking_by_id = AsyncMock(return_value=mock_booking)

    await service.append_message(booking_id, landlord_user, "okay come and visit")

    # Notification must have been dispatched to tenant_id
    service.notification_service.create_notification.assert_called_once_with(
        recipient_id=tenant_id,
        title="New Message from Landlord",
        body="Bachnest Landlord: okay come and visit",
        data={
            "type": "BOOKING_MESSAGE",
            "booking_id": str(booking_id),
            "property_title": "Dhanmondi Master Bed",
        },
    )
