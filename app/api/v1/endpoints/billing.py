"""Billing, Payments, Complaints, Notices, Reviews, Emergency, and Admin API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import ComplaintStatus, PaymentMethod, UserRole
from app.models.emergency import AuditLog
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.booking import (
    CheckoutRequest,
    CheckoutResponse,
    ComplaintCreateRequest,
    ComplaintOut,
    ComplaintStatusUpdate,
    EmergencyAlertOut,
    InvoiceCreateRequest,
    InvoiceOut,
    NoticeCreateRequest,
    NoticeOut,
    NoticeUpdateRequest,
    PaymentOut,
    PaymentWebhookRequest,
    ReviewCreateRequest,
    ReviewOut,
    SOSRequest,
    SOSResolveRequest,
)
from app.schemas.common import StandardResponse
from app.schemas.property import PropertyOut
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService
from app.services.billing_service import BillingService
from app.services.complaint_service import ComplaintService
from app.services.emergency_service import EmergencyService
from app.services.notice_service import NoticeService
from app.services.payment_service import PaymentService
from app.services.review_service import ReviewService

billing_router = APIRouter(prefix="/billing", tags=["Billing & Invoices"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
complaints_router = APIRouter(prefix="/complaints", tags=["Complaints & Maintenance"])
notices_router = APIRouter(tags=["Building Notices"])
reviews_router = APIRouter(prefix="/reviews", tags=["Reviews & Ratings"])
emergency_router = APIRouter(prefix="/emergency", tags=["Emergency SOS"])
admin_router = APIRouter(prefix="/admin", tags=["Admin Operations"])


# --- BILLING & INVOICES ---
@billing_router.post("/invoices", response_model=StandardResponse[InvoiceOut], status_code=status.HTTP_201_CREATED)
async def create_invoice(
    req: InvoiceCreateRequest,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Generate a monthly invoice for an active tenancy."""
    billing_service = BillingService(db)
    invoice = await billing_service.create_invoice(current_user, req)
    return StandardResponse(
        success=True,
        message="Monthly invoice generated successfully",
        data=InvoiceOut.model_validate(invoice),
    )


@billing_router.get("/invoices", response_model=StandardResponse[List[InvoiceOut]])
async def get_my_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve billing invoices for current user (tenant or owner)."""
    billing_service = BillingService(db)
    invoices = await billing_service.list_user_invoices(current_user)
    return StandardResponse(
        success=True,
        message="Invoices retrieved",
        data=[InvoiceOut.model_validate(inv) for inv in invoices],
    )


@billing_router.get("/invoices/{invoice_id}", response_model=StandardResponse[InvoiceOut])
async def get_invoice_by_id(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single invoice details."""
    billing_service = BillingService(db)
    invoice = await billing_service.get_invoice_by_id(invoice_id, current_user)
    return StandardResponse(
        success=True,
        message="Invoice details retrieved",
        data=InvoiceOut.model_validate(invoice),
    )


# --- PAYMENTS ---
@payments_router.post("/checkout", response_model=StandardResponse[CheckoutResponse])
async def initiate_payment_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a payment checkout for an invoice."""
    payment_service = PaymentService(db)
    checkout = await payment_service.initiate_checkout(current_user, req)
    return StandardResponse(
        success=True,
        message="Payment session initialized",
        data=checkout,
    )


@payments_router.post("/webhook", response_model=StandardResponse[PaymentOut])
async def process_payment_webhook(
    req: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    """Idempotent payment webhook handler."""
    payment_service = PaymentService(db)
    payment = await payment_service.process_webhook(req)
    return StandardResponse(
        success=True,
        message="Payment callback processed",
        data=PaymentOut.model_validate(payment),
    )


@payments_router.get("/{payment_id}", response_model=StandardResponse[PaymentOut])
async def get_payment_details(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve payment receipt details."""
    payment_service = PaymentService(db)
    payment = await payment_service.get_payment_by_id(payment_id, current_user)
    return StandardResponse(
        success=True,
        message="Payment receipt retrieved",
        data=PaymentOut.model_validate(payment),
    )


# --- COMPLAINTS ---
@complaints_router.post("", response_model=StandardResponse[ComplaintOut], status_code=status.HTTP_201_CREATED)
async def create_complaint(
    req: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """File a maintenance complaint with SLA deadline."""
    complaint_service = ComplaintService(db)
    complaint = await complaint_service.create_complaint(current_user, req)
    return StandardResponse(
        success=True,
        message="Complaint filed successfully and assigned an SLA deadline",
        data=ComplaintOut.model_validate(complaint),
    )


@complaints_router.get("", response_model=StandardResponse[List[ComplaintOut]])
async def list_complaints(
    status_filter: Optional[ComplaintStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List complaints for tenant, owner, or platform admin."""
    complaint_service = ComplaintService(db)
    complaints = await complaint_service.list_complaints(current_user, status_filter)
    return StandardResponse(
        success=True,
        message="Complaints retrieved",
        data=[ComplaintOut.model_validate(c) for c in complaints],
    )


@complaints_router.get("/{complaint_id}", response_model=StandardResponse[ComplaintOut])
async def get_complaint_details(
    complaint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a maintenance complaint."""
    complaint_service = ComplaintService(db)
    complaint = await complaint_service.get_complaint_by_id(complaint_id, current_user)
    return StandardResponse(
        success=True,
        message="Complaint details retrieved",
        data=ComplaintOut.model_validate(complaint),
    )


@complaints_router.patch("/{complaint_id}/status", response_model=StandardResponse[ComplaintOut])
async def update_complaint_status(
    complaint_id: uuid.UUID,
    req: ComplaintStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Owner or Admin advances complaint resolution status."""
    complaint_service = ComplaintService(db)
    complaint = await complaint_service.update_status(complaint_id, current_user, req)
    return StandardResponse(
        success=True,
        message=f"Complaint status updated to {complaint.status.value}",
        data=ComplaintOut.model_validate(complaint),
    )


@complaints_router.post("/{complaint_id}/reopen", response_model=StandardResponse[ComplaintOut])
async def reopen_complaint(
    complaint_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tenant reopens an unresolved complaint."""
    complaint_service = ComplaintService(db)
    complaint = await complaint_service.reopen_complaint(complaint_id, current_user, reason)
    return StandardResponse(
        success=True,
        message="Complaint reopened for further review",
        data=ComplaintOut.model_validate(complaint),
    )


# --- NOTICES ---
@notices_router.post("/properties/{property_id}/notices", response_model=StandardResponse[NoticeOut], status_code=status.HTTP_201_CREATED)
async def create_property_notice(
    property_id: uuid.UUID,
    req: NoticeCreateRequest,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Owner publishes a building notice."""
    notice_service = NoticeService(db)
    notice = await notice_service.create_notice(property_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Notice published successfully",
        data=NoticeOut.model_validate(notice),
    )


@notices_router.get("/properties/{property_id}/notices", response_model=StandardResponse[List[NoticeOut]])
async def list_property_notices(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List public notices for a building."""
    notice_service = NoticeService(db)
    notices = await notice_service.list_property_notices(property_id)
    return StandardResponse(
        success=True,
        message="Building notices retrieved",
        data=[NoticeOut.model_validate(n) for n in notices],
    )


@notices_router.get("/tenancies/me/notices", response_model=StandardResponse[List[NoticeOut]])
async def list_my_building_notices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve building notices for all properties the tenant currently resides in."""
    notice_service = NoticeService(db)
    notices = await notice_service.list_tenant_notices(current_user)
    return StandardResponse(
        success=True,
        message="Tenant notices retrieved",
        data=notices,
    )


@notices_router.post("/notices/{notice_id}/read", response_model=StandardResponse[dict])
async def mark_notice_as_read(
    notice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record notice read receipt for the current tenant."""
    notice_service = NoticeService(db)
    await notice_service.mark_read(notice_id, current_user)
    return StandardResponse(
        success=True,
        message="Notice marked as read",
        data={"notice_id": str(notice_id)},
    )


# --- REVIEWS ---
@reviews_router.post("", response_model=StandardResponse[ReviewOut], status_code=status.HTTP_201_CREATED)
async def submit_review(
    req: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a two-sided review upon tenancy completion."""
    review_service = ReviewService(db)
    review = await review_service.create_review(current_user, req)
    return StandardResponse(
        success=True,
        message="Review submitted successfully. It will be published once the reciprocal review is submitted.",
        data=ReviewOut.model_validate(review),
    )


@reviews_router.get("/user/{user_id}", response_model=StandardResponse[List[ReviewOut]])
async def get_user_public_reviews(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List public verified reviews for a user."""
    review_service = ReviewService(db)
    reviews = await review_service.list_user_reviews(user_id)
    return StandardResponse(
        success=True,
        message="User reviews retrieved",
        data=[ReviewOut.model_validate(r) for r in reviews],
    )


# --- EMERGENCY SOS ---
@emergency_router.post("/trigger-sos", response_model=StandardResponse[EmergencyAlertOut])
async def trigger_emergency_sos(
    req: SOSRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an Emergency SOS alert broadcasting real-time location to emergency contacts and owner."""
    emergency_service = EmergencyService(db)
    alert = await emergency_service.trigger_sos(current_user, req)
    return StandardResponse(
        success=True,
        message="EMERGENCY ALERT BROADCASTED. Help is on the way.",
        data=EmergencyAlertOut.model_validate(alert),
    )


@emergency_router.get("/{alert_id}", response_model=StandardResponse[EmergencyAlertOut])
async def get_emergency_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a specific SOS alert."""
    emergency_service = EmergencyService(db)
    alert = await emergency_service.get_emergency_by_id(alert_id, current_user)
    return StandardResponse(
        success=True,
        message="Emergency alert details retrieved",
        data=EmergencyAlertOut.model_validate(alert),
    )


@emergency_router.patch("/{alert_id}/resolve", response_model=StandardResponse[EmergencyAlertOut])
async def resolve_emergency_sos(
    alert_id: uuid.UUID,
    req: SOSResolveRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Mark an Emergency alert as resolved."""
    emergency_service = EmergencyService(db)
    alert = await emergency_service.resolve_sos(alert_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Emergency alert resolved",
        data=EmergencyAlertOut.model_validate(alert),
    )


# --- ADMIN DASHBOARD & MODERATION ---
@admin_router.get("/dashboard", response_model=StandardResponse[dict])
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Real platform metrics and administrative overview."""
    admin_service = AdminService(db)
    metrics = await admin_service.get_dashboard_metrics()
    return StandardResponse(
        success=True,
        message="Admin statistics retrieved",
        data=metrics,
    )


@admin_router.get("/users", response_model=StandardResponse[List[UserOut]])
async def list_admin_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List platform users for administration."""
    admin_service = AdminService(db)
    users = await admin_service.list_users(page=page, limit=limit)
    return StandardResponse(
        success=True,
        message="Users retrieved",
        data=[UserOut.model_validate(u) for u in users],
    )


@admin_router.patch("/users/{user_id}/status", response_model=StandardResponse[UserOut])
async def set_user_active_status(
    user_id: uuid.UUID,
    is_active: bool = Query(True),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate user accounts."""
    admin_service = AdminService(db)
    user = await admin_service.set_user_status(user_id, is_active)
    return StandardResponse(
        success=True,
        message=f"User account {'activated' if is_active else 'deactivated'}",
        data=UserOut.model_validate(user),
    )


@admin_router.get("/properties/pending", response_model=StandardResponse[List[PropertyOut]])
async def list_pending_verification_properties(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List unverified properties awaiting admin inspection."""
    admin_service = AdminService(db)
    properties = await admin_service.list_pending_properties()
    return StandardResponse(
        success=True,
        message="Pending verification properties retrieved",
        data=[PropertyOut.model_validate(p) for p in properties],
    )


@admin_router.patch("/properties/{property_id}/verify", response_model=StandardResponse[PropertyOut])
async def verify_property_by_admin(
    property_id: uuid.UUID,
    is_verified: bool = Query(True),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Verify or reject property listings."""
    admin_service = AdminService(db)
    prop = await admin_service.verify_property(property_id, is_verified)
    return StandardResponse(
        success=True,
        message=f"Property {'verified' if is_verified else 'unverified'} by admin",
        data=PropertyOut.model_validate(prop),
    )


@admin_router.get("/audit-logs", response_model=StandardResponse[List[dict]])
async def list_system_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve audit log history."""
    audit_service = AuditService(db)
    logs = await audit_service.list_logs(limit=limit)
    return StandardResponse(
        success=True,
        message="Audit logs retrieved",
        data=[
            {
                "id": str(l.id),
                "actor_id": str(l.actor_id) if l.actor_id else None,
                "action_type": l.action_type.value,
                "entity_name": l.entity_name,
                "entity_id": str(l.entity_id) if l.entity_id else None,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
    )
