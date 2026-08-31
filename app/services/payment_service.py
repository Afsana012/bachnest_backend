"""Payment service managing checkout sessions, webhook verification, and invoice status reconciliation."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import InvoiceStatus, PaymentMethod, PaymentStatus, UserRole
from app.core.exceptions import ConflictError, InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.integrations.payments.mock_gateway import MockPaymentGateway
from app.models.invoice import Invoice, Payment
from app.models.user import User
from app.schemas.booking import CheckoutRequest, CheckoutResponse, PaymentWebhookRequest


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gateway = MockPaymentGateway()

    async def initiate_checkout(self, user: User, req: CheckoutRequest) -> CheckoutResponse:
        """Create a payment session for an open invoice."""
        inv_query = select(Invoice).where(Invoice.id == req.invoice_id).with_for_update()
        invoice = (await self.db.execute(inv_query)).scalar_one_or_none()
        if not invoice:
            raise ResourceNotFoundError(message="Invoice not found")

        if invoice.tenant_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You can only pay for your own invoices")

        if invoice.status == InvoiceStatus.PAID:
            raise ConflictError(message="This invoice has already been fully paid")

        remaining_balance = invoice.total_amount - invoice.paid_amount
        txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        payment = Payment(
            invoice_id=invoice.id,
            tenant_id=user.id,
            transaction_reference=txn_ref,
            amount=remaining_balance,
            payment_method=req.payment_method,
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)

        payment_url = await self.gateway.create_checkout(
            payment_id=payment.id,
            amount=payment.amount,
            transaction_ref=txn_ref,
        )

        return CheckoutResponse(
            payment_id=payment.id,
            transaction_reference=txn_ref,
            amount=payment.amount,
            payment_url=payment_url,
        )

    async def process_webhook(self, req: PaymentWebhookRequest) -> Payment:
        """Handle idempotent payment callback and update invoice balance."""
        pay_query = select(Payment).where(Payment.transaction_reference == req.transaction_reference).with_for_update()
        payment = (await self.db.execute(pay_query)).scalar_one_or_none()
        if not payment:
            raise ResourceNotFoundError(message="Payment transaction not found")

        # Idempotency: If already completed or failed with final state, return without double-crediting
        if payment.status == PaymentStatus.COMPLETED:
            return payment

        # Verify with gateway
        is_valid = await self.gateway.verify_webhook(
            transaction_ref=req.transaction_reference,
            amount=payment.amount,
            signature=req.signature,
        )
        if not is_valid:
            payment.status = PaymentStatus.FAILED
            await self.db.flush()
            return payment

        if req.status == PaymentStatus.COMPLETED:
            payment.status = PaymentStatus.COMPLETED
            payment.gateway_transaction_id = req.gateway_transaction_id or f"GW-{uuid.uuid4().hex[:8].upper()}"
            payment.paid_at = datetime.now(timezone.utc)

            # Update Invoice
            inv_query = select(Invoice).where(Invoice.id == payment.invoice_id).with_for_update()
            invoice = (await self.db.execute(inv_query)).scalar_one_or_none()
            if invoice:
                invoice.paid_amount = invoice.paid_amount + payment.amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = InvoiceStatus.PAID
                elif invoice.paid_amount > Decimal("0.0"):
                    invoice.status = InvoiceStatus.PARTIALLY_PAID

        elif req.status == PaymentStatus.FAILED:
            payment.status = PaymentStatus.FAILED

        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def get_payment_by_id(self, payment_id: uuid.UUID, user: User) -> Payment:
        """Retrieve payment record with authorization check."""
        query = select(Payment).where(Payment.id == payment_id)
        payment = (await self.db.execute(query)).scalar_one_or_none()
        if not payment:
            raise ResourceNotFoundError(message="Payment record not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN) and payment.tenant_id != user.id:
            raise PermissionDeniedError(message="You do not have access to this payment record")

        return payment
