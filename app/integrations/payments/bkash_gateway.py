"""bKash Tokenized Checkout v1.2.0-beta payment gateway integration."""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
import uuid

import httpx

from app.core.config import settings
from app.core.exceptions import BadRequestError


class BkashGateway:
    """bKash Tokenized Checkout API client with automatic token management."""

    _id_token: Optional[str] = None
    _token_expiry: Optional[datetime] = None
    _lock = asyncio.Lock()

    async def _get_token(self) -> str:
        """Return a cached bKash ID token, refreshing if expired or absent."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            if self._id_token and self._token_expiry and now < self._token_expiry:
                return self._id_token

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{settings.BKASH_BASE_URL}/tokenized/checkout/token/grant",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "username": settings.BKASH_USERNAME,
                        "password": settings.BKASH_PASSWORD,
                    },
                    json={
                        "app_key": settings.BKASH_APP_KEY,
                        "app_secret": settings.BKASH_APP_SECRET,
                    },
                )

            data = response.json()
            if data.get("statusCode") != "0000":
                raise BadRequestError(
                    message=f"bKash token grant failed: {data.get('statusMessage', 'Unknown error')}"
                )

            BkashGateway._id_token = data["id_token"]
            # Token is valid for 3600s; cache for 50 min to avoid edge-case expiry
            BkashGateway._token_expiry = now + timedelta(minutes=50)
            return BkashGateway._id_token

    async def create_payment(
        self,
        invoice_id: uuid.UUID,
        amount: Decimal,
        merchant_invoice_number: str,
    ) -> dict:
        """Initiate a bKash payment and return paymentID + bkashURL."""
        token = await self._get_token()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.BKASH_BASE_URL}/tokenized/checkout/create",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": token,
                    "X-APP-Key": settings.BKASH_APP_KEY,
                },
                json={
                    "mode": "0011",
                    "payerReference": str(invoice_id),
                    "callbackURL": settings.BKASH_CALLBACK_URL,
                    "amount": str(amount),
                    "currency": "BDT",
                    "intent": "sale",
                    "merchantInvoiceNumber": merchant_invoice_number,
                },
            )

        data = response.json()
        if data.get("statusCode") != "0000":
            raise BadRequestError(
                message=f"bKash payment creation failed: {data.get('statusMessage', 'Unknown error')}"
            )

        return {
            "payment_id": data["paymentID"],
            "bkash_url": data["bkashURL"],
        }

    async def execute_payment(self, payment_id: str) -> dict:
        """Execute a payment after user completes bKash OTP/PIN flow."""
        token = await self._get_token()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.BKASH_BASE_URL}/tokenized/checkout/execute",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": token,
                    "X-APP-Key": settings.BKASH_APP_KEY,
                },
                json={"paymentID": payment_id},
            )

        data = response.json()
        if data.get("statusCode") != "0000":
            raise BadRequestError(
                message=f"bKash payment execution failed: {data.get('statusMessage', 'Unknown error')}"
            )

        return {
            "payment_id": data["paymentID"],
            "trx_id": data["trxID"],
            "transaction_status": data["transactionStatus"],
            "amount": data["amount"],
            "currency": data["currency"],
            "customer_msisdn": data.get("customerMsisdn", ""),
            "merchant_invoice_number": data.get("merchantInvoiceNumber", ""),
        }

    async def query_payment(self, payment_id: str) -> dict:
        """Query the current status of a bKash payment."""
        token = await self._get_token()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.BKASH_BASE_URL}/tokenized/checkout/payment/status",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": token,
                    "X-APP-Key": settings.BKASH_APP_KEY,
                },
                json={"paymentID": payment_id},
            )

        return response.json()
