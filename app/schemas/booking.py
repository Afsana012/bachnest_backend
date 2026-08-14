"""Booking, Tenancy, Billing, Payment, Complaint, and Emergency schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from app.core.constants import (
    AgreementStatus,
    BookingStatus,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    EmergencyType,
    InvoiceStatus,
    NoticePriority,
    PaymentMethod,
    PaymentStatus,
    TenancyStatus,
)
from app.schemas.common import BaseSchema


# --- BOOKING ---
class BookingCreateRequest(BaseSchema):
    property_id: uuid.UUID
    room_id: uuid.UUID
    seat_id: Optional[uuid.UUID] = None
    requested_move_in_date: date
    token_deposit_amount: Decimal = Field(default=Decimal("0.0"), ge=0)


class BookingDecisionRequest(BaseSchema):
    decision: str = Field(..., description="APPROVE or REJECT")
    reason: Optional[str] = None


class BookingOut(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    property_id: uuid.UUID
    room_id: uuid.UUID
    seat_id: Optional[uuid.UUID] = None
    booking_status: BookingStatus
    requested_move_in_date: date
    token_deposit_amount: Decimal
    owner_remarks: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime


# --- TENANCY ---
class TenancyOut(BaseSchema):
    id: uuid.UUID
    booking_id: Optional[uuid.UUID] = None
    tenant_id: uuid.UUID
    owner_id: uuid.UUID
    property_id: uuid.UUID
    room_id: uuid.UUID
    seat_id: Optional[uuid.UUID] = None
    agreed_monthly_rent: Decimal
    agreed_security_deposit: Decimal
    lease_start_date: date
    lease_end_date: Optional[date] = None
    notice_period_days: int
    status: TenancyStatus
    agreement_status: AgreementStatus
    digital_agreement_url: Optional[str] = None
    created_at: datetime


class TenancyNoticeRequest(BaseSchema):
    notice_reason: str = Field(..., min_length=5)
    move_out_date: date


# --- BILLING & INVOICE ---
class InvoiceCreateRequest(BaseSchema):
    tenancy_id: uuid.UUID
    billing_month_year: str = Field(..., description="YYYY-MM e.g. 2026-09")
    base_rent: Decimal = Field(..., ge=0)
    service_charge: Decimal = Field(default=Decimal("0.0"), ge=0)
    electricity_bill: Decimal = Field(default=Decimal("0.0"), ge=0)
    water_bill: Decimal = Field(default=Decimal("0.0"), ge=0)
    gas_bill: Decimal = Field(default=Decimal("0.0"), ge=0)
    internet_bill: Decimal = Field(default=Decimal("0.0"), ge=0)
    other_adjustments: Decimal = Field(default=Decimal("0.0"))
    due_date: date


class InvoiceOut(BaseSchema):
    id: uuid.UUID
    invoice_number: str
    tenancy_id: uuid.UUID
    tenant_id: uuid.UUID
    billing_month_year: str
    base_rent: Decimal
    service_charge: Decimal
    electricity_bill: Decimal
    water_bill: Decimal
    gas_bill: Decimal
    internet_bill: Decimal
    other_adjustments: Decimal
    late_fee: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    due_date: date
    status: InvoiceStatus
    created_at: datetime


# --- PAYMENTS ---
class CheckoutRequest(BaseSchema):
    invoice_id: uuid.UUID
    payment_method: PaymentMethod = PaymentMethod.MOCK


class CheckoutResponse(BaseSchema):
    payment_id: uuid.UUID
    transaction_reference: str
    amount: Decimal
    payment_url: Optional[str] = None


class PaymentWebhookRequest(BaseSchema):
    transaction_reference: str
    status: PaymentStatus
    gateway_transaction_id: Optional[str] = None
    signature: Optional[str] = None


class PaymentOut(BaseSchema):
    id: uuid.UUID
    invoice_id: uuid.UUID
    tenant_id: uuid.UUID
    transaction_reference: str
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime


# --- COMPLAINTS ---
class ComplaintCreateRequest(BaseSchema):
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: ComplaintCategory = ComplaintCategory.OTHER
    priority: ComplaintPriority = ComplaintPriority.MEDIUM
    evidence_urls: List[str] = Field(default_factory=list)


class ComplaintStatusUpdate(BaseSchema):
    status: ComplaintStatus
    resolution_notes: Optional[str] = None
    repair_cost: Optional[Decimal] = None
    cost_bearer: Optional[str] = None


class ComplaintOut(BaseSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    tenancy_id: Optional[uuid.UUID] = None
    tenant_id: uuid.UUID
    title: str
    description: str
    category: ComplaintCategory
    priority: ComplaintPriority
    status: ComplaintStatus
    sla_deadline: datetime
    evidence_urls: Optional[List[str]] = None
    repair_cost: Optional[Decimal] = None
    cost_bearer: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


# --- EMERGENCY ---
class SOSRequest(BaseSchema):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    alert_type: EmergencyType = EmergencyType.OTHER
    emergency_message: Optional[str] = None


class EmergencyAlertOut(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    property_id: Optional[uuid.UUID] = None
    alert_type: EmergencyType
    emergency_message: Optional[str] = None
    latitude: float
    longitude: float
    is_active: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime
