"""Billing service managing monthly invoices, utility calculations, and due dates."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import InvoiceStatus, TenancyStatus, UserRole
from app.core.exceptions import ConflictError, InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.booking import InvoiceCreateRequest


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_total(
        self,
        base_rent: Decimal,
        service_charge: Decimal = Decimal("0.0"),
        electricity: Decimal = Decimal("0.0"),
        water: Decimal = Decimal("0.0"),
        gas: Decimal = Decimal("0.0"),
        internet: Decimal = Decimal("0.0"),
        adjustments: Decimal = Decimal("0.0"),
        late_fee: Decimal = Decimal("0.0"),
    ) -> Decimal:
        """Calculate exact invoice total using Decimal arithmetic."""
        total = (
            Decimal(str(base_rent))
            + Decimal(str(service_charge))
            + Decimal(str(electricity))
            + Decimal(str(water))
            + Decimal(str(gas))
            + Decimal(str(internet))
            + Decimal(str(adjustments))
            + Decimal(str(late_fee))
        )
        return total.quantize(Decimal("0.01"))

    async def create_invoice(self, owner: User, req: InvoiceCreateRequest) -> Invoice:
        """Generate a new monthly invoice for an active tenancy."""
        # 1. Verify Tenancy
        tenancy_query = select(Tenancy).where(Tenancy.id == req.tenancy_id)
        tenancy = (await self.db.execute(tenancy_query)).scalar_one_or_none()
        if not tenancy:
            raise ResourceNotFoundError(message="Tenancy not found")

        if tenancy.owner_id != owner.id and owner.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this tenancy")

        if tenancy.status not in (TenancyStatus.ACTIVE, TenancyStatus.NOTICE_SERVED):
            raise InvalidBookingError(message=f"Cannot generate invoice for tenancy in status {tenancy.status.value}")

        # 2. Check for duplicate invoice in same billing month
        dup_query = select(Invoice).where(
            Invoice.tenancy_id == req.tenancy_id,
            Invoice.billing_month_year == req.billing_month_year
        )
        dup_invoice = (await self.db.execute(dup_query)).scalar_one_or_none()
        if dup_invoice:
            raise ConflictError(message=f"Invoice for period {req.billing_month_year} already exists for this tenancy")

        # 3. Calculate total
        total = self.calculate_total(
            base_rent=req.base_rent,
            service_charge=req.service_charge,
            electricity=req.electricity_bill,
            water=req.water_bill,
            gas=req.gas_bill,
            internet=req.internet_bill,
            adjustments=req.other_adjustments,
        )

        inv_num = f"INV-{req.billing_month_year.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}"

        invoice = Invoice(
            tenancy_id=tenancy.id,
            tenant_id=tenancy.tenant_id,
            invoice_number=inv_num,
            billing_month_year=req.billing_month_year,
            base_rent=req.base_rent,
            service_charge=req.service_charge,
            electricity_bill=req.electricity_bill,
            water_bill=req.water_bill,
            gas_bill=req.gas_bill,
            internet_bill=req.internet_bill,
            other_adjustments=req.other_adjustments,
            late_fee=Decimal("0.0"),
            total_amount=total,
            paid_amount=Decimal("0.0"),
            due_date=req.due_date,
            status=InvoiceStatus.ISSUED,
        )
        self.db.add(invoice)
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def get_invoice_by_id(self, invoice_id: uuid.UUID, user: User) -> Invoice:
        """Retrieve invoice details with authorization check."""
        query = select(Invoice).where(Invoice.id == invoice_id)
        invoice = (await self.db.execute(query)).scalar_one_or_none()
        if not invoice:
            raise ResourceNotFoundError(message="Invoice not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            # Check if user is tenant or property owner
            tenancy_query = select(Tenancy).where(Tenancy.id == invoice.tenancy_id)
            tenancy = (await self.db.execute(tenancy_query)).scalar_one_or_none()
            if invoice.tenant_id != user.id and (not tenancy or tenancy.owner_id != user.id):
                raise PermissionDeniedError(message="You do not have access to this invoice")

        return invoice

    async def list_user_invoices(self, user: User) -> List[Invoice]:
        """List invoices for tenant or owner."""
        if user.role == UserRole.OWNER:
            query = (
                select(Invoice)
                .join(Tenancy, Tenancy.id == Invoice.tenancy_id)
                .where(Tenancy.owner_id == user.id)
                .order_by(Invoice.created_at.desc())
            )
        elif user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            query = select(Invoice).order_by(Invoice.created_at.desc())
        else:
            query = select(Invoice).where(Invoice.tenant_id == user.id).order_by(Invoice.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
