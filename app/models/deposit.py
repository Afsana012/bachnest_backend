"""Deposit refund claim domain model."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DepositRefundStatus, PayoutMethod
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DepositRefundClaim(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "deposit_refund_claims"

    tenancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenancies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[DepositRefundStatus] = mapped_column(
        SQLEnum(DepositRefundStatus, name="deposit_refund_status_enum"),
        nullable=False,
        default=DepositRefundStatus.REQUESTED,
        index=True
    )
    total_deposit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    requested_refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deduction_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    net_refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deduction_breakdown: Mapped[List[Any]] = mapped_column(JSONB, nullable=False, default=list)
    tenant_payout_method: Mapped[str] = mapped_column(String(50), nullable=False, default="BKASH")
    tenant_payout_account: Mapped[str] = mapped_column(String(100), nullable=False)
    move_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenant_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    landlord_remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenancy = relationship("Tenancy", backref="deposit_refund_claims")
    tenant = relationship("User", foreign_keys=[tenant_id], backref="deposit_claims_as_tenant")
    owner = relationship("User", foreign_keys=[owner_id], backref="deposit_claims_as_owner")
