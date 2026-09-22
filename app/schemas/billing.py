"""Billing-specific Pydantic response schemas."""

import uuid
from decimal import Decimal

from app.schemas.common import BaseSchema


class BkashInitiateResponse(BaseSchema):
    payment_id: uuid.UUID
    transaction_reference: str
    amount: Decimal
    bkash_url: str
