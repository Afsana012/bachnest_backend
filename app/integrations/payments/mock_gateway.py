"""Mock Payment Gateway implementation for sandbox and local testing."""

from decimal import Decimal
from typing import Optional
import uuid


class MockPaymentGateway:
    async def create_checkout(self, payment_id: uuid.UUID, amount: Decimal, transaction_ref: str) -> str:
        """Return simulated sandbox payment checkout URL."""
        return f"https://sandbox.bachnest.com/pay/{transaction_ref}"

    async def verify_webhook(self, transaction_ref: str, amount: Decimal, signature: Optional[str] = None) -> bool:
        """Validate simulated payment webhook."""
        # For mock sandbox, accept valid transaction reference prefix
        if transaction_ref.startswith("TXN-"):
            return True
        return False
