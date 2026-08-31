"""Payment gateway adapter interface."""

from decimal import Decimal
from typing import Optional, Protocol
import uuid


class PaymentGateway(Protocol):
    async def create_checkout(self, payment_id: uuid.UUID, amount: Decimal, transaction_ref: str) -> str:
        """Initialize a payment checkout session and return the redirect URL."""
        ...

    async def verify_webhook(self, transaction_ref: str, amount: Decimal, signature: Optional[str] = None) -> bool:
        """Verify webhook signature and authenticity."""
        ...
