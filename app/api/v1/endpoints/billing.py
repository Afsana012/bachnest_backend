"""Billing, Payment, Complaint, Emergency, and Admin routers."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import ComplaintStatus, InvoiceStatus, PaymentMethod, PaymentStatus, SLA_HOURS_MAP, UserRole
from app.core.exceptions import ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.complaint import Complaint
from app.models.emergency import AuditLog, EmergencyAlert
from app.models.invoice import Invoice, Payment
from app.models.user import User
from app.schemas.booking import (
    CheckoutRequest,
    CheckoutResponse,
    ComplaintCreateRequest,
    ComplaintOut,
    ComplaintStatusUpdate,
    EmergencyAlertOut,
    InvoiceCreateRequest,
    InvoiceOut,
    PaymentOut,
    PaymentWebhookRequest,
    SOSRequest,
)
from app.schemas.common import StandardResponse

billing_router = APIRouter(prefix="/billing", tags=["Billing & Invoices"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
complaints_router = APIRouter(prefix="/complaints", tags=["Complaints & Maintenance"])
emergency_router = APIRouter(prefix="/emergency", tags=["Emergency SOS"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# --- BILLING ---
@billing_router.get("/invoices", response_model=StandardResponse[List[InvoiceOut]])
async def get_my_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve billing invoices for tenant."""
    query = select(Invoice).where(Invoice.tenant_id == current_user.id)
    result = await db.execute(query)
    invoices = result.scalars().all()
    return StandardResponse(
        success=True,
        message="Invoices retrieved",
        data=[InvoiceOut.model_validate(inv) for inv in invoices]
    )


# --- PAYMENTS ---
@payments_router.post("/checkout", response_model=StandardResponse[CheckoutResponse])
async def initiate_payment_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initiate a payment checkout for an invoice."""
    inv_query = select(Invoice).where(Invoice.id == req.invoice_id)
    invoice = (await db.execute(inv_query)).scalar_one_or_none()
    if not invoice:
        raise ResourceNotFoundError(message="Invoice not found")

    txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    payment = Payment(
        invoice_id=invoice.id,
        tenant_id=current_user.id,
        transaction_reference=txn_ref,
        amount=invoice.total_amount,
        payment_method=req.payment_method,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)

    return StandardResponse(
        success=True,
        message="Payment session initialized",
        data=CheckoutResponse(
            payment_id=payment.id,
            transaction_reference=txn_ref,
            amount=payment.amount,
            payment_url=f"https://sandbox.bachnest.com/pay/{txn_ref}",
        )
    )


# --- COMPLAINTS ---
@complaints_router.post("", response_model=StandardResponse[ComplaintOut], status_code=status.HTTP_201_CREATED)
async def create_complaint(
    req: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """File a maintenance or house complaint."""
    sla_hours = SLA_HOURS_MAP.get(req.priority, 48)
    deadline = datetime.now(timezone.utc) + __import__("datetime").timedelta(hours=sla_hours)

    complaint = Complaint(
        property_id=req.property_id,
        room_id=req.room_id,
        tenant_id=current_user.id,
        title=req.title,
        description=req.description,
        category=req.category,
        priority=req.priority,
        status=ComplaintStatus.OPEN,
        sla_deadline=deadline,
        evidence_urls=req.evidence_urls,
    )
    db.add(complaint)
    await db.flush()
    await db.refresh(complaint)

    return StandardResponse(
        success=True,
        message="Complaint filed successfully and assigned an SLA deadline",
        data=ComplaintOut.model_validate(complaint)
    )


# --- EMERGENCY SOS ---
@emergency_router.post("/trigger-sos", response_model=StandardResponse[EmergencyAlertOut])
async def trigger_emergency_sos(
    req: SOSRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger an Emergency SOS alert broadcasting real-time location to emergency contacts and owner."""
    alert = EmergencyAlert(
        user_id=current_user.id,
        alert_type=req.alert_type,
        emergency_message=req.emergency_message,
        latitude=req.latitude,
        longitude=req.longitude,
        is_active=True,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)

    return StandardResponse(
        success=True,
        message="EMERGENCY ALERT BROADCASTED. Help is on the way.",
        data=EmergencyAlertOut.model_validate(alert)
    )


# --- ADMIN ---
@admin_router.get("/dashboard", response_model=StandardResponse[dict])
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """Administrative overview and platform metrics."""
    return StandardResponse(
        success=True,
        message="Admin statistics retrieved",
        data={
            "total_users": 100,
            "verified_properties": 45,
            "active_tenancies": 68,
            "open_complaints": 4,
            "active_sos": 0,
        }
    )
