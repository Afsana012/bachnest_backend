"""Unit tests for bKash payment gateway integration."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.constants import InvoiceStatus, PaymentMethod, PaymentStatus
from app.schemas.billing import BkashInitiateResponse


# --- Schema Tests ---

def test_bkash_initiate_response_schema():
    resp = BkashInitiateResponse(
        payment_id=uuid.uuid4(),
        transaction_reference="BK-ABC123DEF456",
        amount=Decimal("5000.00"),
        bkash_url="https://sandbox.payment.bkash.com/?paymentId=TR001&hash=abc",
    )
    assert resp.amount == Decimal("5000.00")
    assert resp.bkash_url.startswith("https://")
    assert resp.transaction_reference.startswith("BK-")


def test_bkash_initiate_response_serialization():
    resp = BkashInitiateResponse(
        payment_id=uuid.uuid4(),
        transaction_reference="BK-XYZ999",
        amount=Decimal("12500.50"),
        bkash_url="https://tokenized.sandbox.bka.sh/checkout?paymentId=TR002",
    )
    data = resp.model_dump()
    assert "payment_id" in data
    assert "bkash_url" in data
    assert data["amount"] == Decimal("12500.50")


# --- Gateway Token Cache Tests ---

def test_bkash_gateway_token_cache_attributes():
    """BkashGateway class must have class-level token cache attributes."""
    from app.integrations.payments.bkash_gateway import BkashGateway

    assert hasattr(BkashGateway, "_id_token")
    assert hasattr(BkashGateway, "_token_expiry")
    assert hasattr(BkashGateway, "_lock")


@pytest.mark.asyncio
async def test_bkash_gateway_get_token_caches_result():
    """_get_token should reuse cached token if within 50-minute window."""
    from app.integrations.payments.bkash_gateway import BkashGateway

    gateway = BkashGateway()
    future_expiry = datetime.now(timezone.utc) + timedelta(minutes=40)
    BkashGateway._id_token = "cached-test-token"
    BkashGateway._token_expiry = future_expiry

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        token = await gateway._get_token()

    assert token == "cached-test-token"
    mock_post.assert_not_called()

    # Cleanup
    BkashGateway._id_token = None
    BkashGateway._token_expiry = None


@pytest.mark.asyncio
async def test_bkash_gateway_fetches_new_token_when_expired():
    """_get_token should request a new token when cache is expired."""
    from app.integrations.payments.bkash_gateway import BkashGateway

    gateway = BkashGateway()
    BkashGateway._id_token = "old-expired-token"
    BkashGateway._token_expiry = datetime.now(timezone.utc) - timedelta(minutes=5)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "statusCode": "0000",
        "id_token": "fresh-token-xyz",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "refresh-abc",
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        token = await gateway._get_token()

    assert token == "fresh-token-xyz"
    assert BkashGateway._id_token == "fresh-token-xyz"

    # Cleanup
    BkashGateway._id_token = None
    BkashGateway._token_expiry = None


# --- Service Logic Tests ---

@pytest.mark.asyncio
async def test_bkash_service_initiate_raises_on_paid_invoice():
    """BkashService.initiate must raise ConflictError when invoice is already PAID."""
    from app.services.bkash_service import BkashService
    from app.core.exceptions import ConflictError

    db = AsyncMock()
    paid_invoice = MagicMock()
    paid_invoice.id = uuid.uuid4()
    paid_invoice.tenant_id = uuid.uuid4()
    paid_invoice.status = InvoiceStatus.PAID
    paid_invoice.total_amount = Decimal("5000.00")
    paid_invoice.paid_amount = Decimal("5000.00")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = paid_invoice
    db.execute = AsyncMock(return_value=mock_result)

    user = MagicMock()
    user.id = paid_invoice.tenant_id
    user.role = MagicMock(value="BACHELOR")

    service = BkashService(db)
    with pytest.raises(ConflictError):
        await service.initiate(paid_invoice.id, user)


@pytest.mark.asyncio
async def test_bkash_service_callback_marks_failed_on_cancel():
    """execute_callback must mark payment FAILED when status is 'cancel'."""
    from app.services.bkash_service import BkashService

    db = AsyncMock()
    pending_payment = MagicMock()
    pending_payment.status = PaymentStatus.PENDING
    pending_payment.payment_method = PaymentMethod.BKASH

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = pending_payment
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    service = BkashService(db)
    result = await service.execute_callback("bkash-pay-id-123", "cancel")

    assert result.status == PaymentStatus.FAILED
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_bkash_service_callback_marks_failed_on_failure_status():
    """execute_callback must mark payment FAILED when status is 'failure'."""
    from app.services.bkash_service import BkashService

    db = AsyncMock()
    pending_payment = MagicMock()
    pending_payment.status = PaymentStatus.PENDING
    pending_payment.payment_method = PaymentMethod.BKASH

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = pending_payment
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()

    service = BkashService(db)
    result = await service.execute_callback("bkash-pay-id-456", "failure")

    assert result.status == PaymentStatus.FAILED
