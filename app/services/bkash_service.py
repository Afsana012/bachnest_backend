"""bKash payment service — orchestrates invoice lookup, Payment record creation, and gateway calls."""

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import InvoiceStatus, PaymentMethod, PaymentStatus, UserRole
from app.core.exceptions import BadRequestError, ConflictError, PermissionDeniedError, ResourceNotFoundError
from app.integrations.payments.bkash_gateway import BkashGateway
from app.models.invoice import Invoice, Payment
from app.models.user import User
from app.schemas.billing import BkashInitiateResponse


class BkashService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gateway = BkashGateway()

    async def initiate(self, invoice_id: uuid.UUID, user: User) -> BkashInitiateResponse:
        """Create a bKash payment session for an open invoice and return the redirect URL."""
        invoice = await self._get_open_invoice(invoice_id, user)

        remaining = invoice.total_amount - invoice.paid_amount
        txn_ref = f"BK-{uuid.uuid4().hex[:12].upper()}"

        payment = Payment(
            invoice_id=invoice.id,
            tenant_id=user.id,
            transaction_reference=txn_ref,
            amount=remaining,
            payment_method=PaymentMethod.BKASH,
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)

        bkash_data = await self.gateway.create_payment(
            invoice_id=invoice.id,
            amount=remaining,
            merchant_invoice_number=invoice.invoice_number,
        )

        payment.gateway_transaction_id = bkash_data["payment_id"]
        payment.payment_gateway_response = {"bkash_payment_id": bkash_data["payment_id"]}
        await self.db.flush()

        return BkashInitiateResponse(
            payment_id=payment.id,
            transaction_reference=txn_ref,
            amount=remaining,
            bkash_url=bkash_data["bkash_url"],
        )

    async def execute_callback(self, bkash_payment_id: str, status: str) -> Payment:
        """Handle bKash redirect callback: execute payment if approved, mark failed otherwise."""
        pay_query = select(Payment).where(
            Payment.gateway_transaction_id == bkash_payment_id,
            Payment.payment_method == PaymentMethod.BKASH,
        ).with_for_update()
        payment = (await self.db.execute(pay_query)).scalar_one_or_none()

        if not payment:
            raise ResourceNotFoundError(message="Payment record not found for this bKash session")

        if payment.status == PaymentStatus.COMPLETED:
            return payment

        if status.lower() in ("cancel", "failure"):
            payment.status = PaymentStatus.FAILED
            await self.db.flush()
            return payment

        result = await self.gateway.execute_payment(bkash_payment_id)

        if result.get("transaction_status") != "Completed":
            payment.status = PaymentStatus.FAILED
            payment.payment_gateway_response = result
            await self.db.flush()
            return payment

        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = datetime.now(timezone.utc)
        payment.payment_gateway_response = result
        payment.gateway_transaction_id = result["trx_id"]
        payment.receipt_url = (
            f"{settings.FRONTEND_APP_URL}/payments/{payment.id}/receipt"
        )

        inv_query = select(Invoice).where(Invoice.id == payment.invoice_id).with_for_update()
        invoice = (await self.db.execute(inv_query)).scalar_one_or_none()
        if invoice:
            invoice.paid_amount = invoice.paid_amount + payment.amount
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = InvoiceStatus.PAID
            elif invoice.paid_amount > Decimal("0.0"):
                invoice.status = InvoiceStatus.PARTIALLY_PAID

        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def _get_open_invoice(self, invoice_id: uuid.UUID, user: User) -> Invoice:
        query = select(Invoice).where(Invoice.id == invoice_id).with_for_update()
        invoice = (await self.db.execute(query)).scalar_one_or_none()
        if not invoice:
            raise ResourceNotFoundError(message="Invoice not found")
        if invoice.tenant_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You can only pay for your own invoices")
        if invoice.status == InvoiceStatus.PAID:
            raise ConflictError(message="This invoice has already been fully paid")
        return invoice
