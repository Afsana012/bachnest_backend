"""Invoice and Payment domain models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import InvoiceStatus, PaymentMethod, PaymentStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenancy_id", "billing_month_year", name="uq_tenancy_billing_month"),
    )

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
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
    billing_month_year: Mapped[str] = mapped_column(String(7), nullable=False)  # "YYYY-MM" e.g., "2026-09"
    
    # Financial breakdown (BDT)
    base_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    service_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    electricity_bill: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    water_bill: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    gas_bill: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    internet_bill: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    other_adjustments: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    late_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus, name="invoice_status_enum"),
        default=InvoiceStatus.ISSUED,
        nullable=False,
        index=True
    )

    # Relationships
    tenancy = relationship("Tenancy", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transaction_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod, name="payment_method_enum"),
        default=PaymentMethod.MOCK,
        nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_gateway_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
