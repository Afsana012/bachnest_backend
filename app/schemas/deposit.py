"""Pydantic schemas for Security Deposit Refund and Settlement."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.core.constants import DepositRefundStatus


class DeductionItem(BaseModel):
    reason: str = Field(..., min_length=2, max_length=255)
    amount: Decimal = Field(..., ge=0)
    note: Optional[str] = None


class DepositClaimCreate(BaseModel):
    tenancy_id: uuid.UUID
    tenant_payout_method: str = Field("BKASH", max_length=50)
    tenant_payout_account: str = Field(..., min_length=5, max_length=100)
    move_out_date: date
    tenant_notes: Optional[str] = Field(None, max_length=500)


class DepositClaimSettle(BaseModel):
    deductions: List[DeductionItem] = Field(default_factory=list)
    transaction_reference: Optional[str] = Field(None, max_length=100)
    landlord_remarks: Optional[str] = Field(None, max_length=500)


class DepositClaimOut(BaseModel):
    id: uuid.UUID
    tenancy_id: uuid.UUID
    tenant_id: uuid.UUID
    owner_id: uuid.UUID
    status: DepositRefundStatus
    total_deposit_amount: Decimal
    requested_refund_amount: Decimal
    deduction_amount: Decimal
    net_refund_amount: Decimal
    deduction_breakdown: List[Any]
    tenant_payout_method: str
    tenant_payout_account: str
    move_out_date: date
    tenant_notes: Optional[str] = None
    landlord_remarks: Optional[str] = None
    transaction_reference: Optional[str] = None
    settled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    property_title: Optional[str] = None
    room_name: Optional[str] = None
    tenant_name: Optional[str] = None
    owner_name: Optional[str] = None

    class Config:
        from_attributes = True
