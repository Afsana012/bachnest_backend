"""Payment gateway protocol and Mock Gateway implementation."""

import uuid
from decimal import Decimal
from typing import Any, Dict, Optional, Protocol


class PaymentGateway(Protocol):
    async def create_checkout(self, amount: Decimal, transaction_reference: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def verify_payment(self, callback_data: Dict[str, Any]) -> bool:
        ...


class MockPaymentGateway:
    async def create_checkout(self, amount: Decimal, transaction_reference: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "gateway": "MOCK",
            "transaction_reference": transaction_reference,
            "amount": str(amount),
            "payment_url": f"https://mockpay.bachnest.com/pay/{transaction_reference}",
            "status": "INITIATED"
        }

    async def verify_payment(self, callback_data: Dict[str, Any]) -> bool:
        return callback_data.get("status") in ["COMPLETED", "SUCCESS", "PAID"]
