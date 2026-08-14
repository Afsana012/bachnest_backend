"""Booking and Tenancy domain models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AgreementStatus, BookingStatus, TenancyStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bookings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    seat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_seats.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    booking_status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name="booking_status_enum"),
        default=BookingStatus.REQUESTED,
        nullable=False,
        index=True
    )
    requested_move_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    token_deposit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    owner_remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    tenant = relationship("User", back_populates="bookings", foreign_keys=[tenant_id])
    property = relationship("Property", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    seat = relationship("RoomSeat", back_populates="bookings")
    tenancy = relationship("Tenancy", back_populates="booking", uselist=False)


class Tenancy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenancies"

    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        unique=True,
        nullable=True
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
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    seat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_seats.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    agreed_monthly_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    agreed_security_deposit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lease_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    lease_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notice_period_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    status: Mapped[TenancyStatus] = mapped_column(
        SQLEnum(TenancyStatus, name="tenancy_status_enum"),
        default=TenancyStatus.ACTIVE,
        nullable=False,
        index=True
    )
    agreement_status: Mapped[AgreementStatus] = mapped_column(
        SQLEnum(AgreementStatus, name="agreement_status_enum"),
        default=AgreementStatus.DRAFT,
        nullable=False
    )
    digital_agreement_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="tenancy")
    tenant = relationship("User", back_populates="tenancies_as_tenant", foreign_keys=[tenant_id])
    owner = relationship("User", back_populates="tenancies_as_owner", foreign_keys=[owner_id])
    property = relationship("Property", back_populates="tenancies")
    room = relationship("Room", back_populates="tenancies")
    seat = relationship("RoomSeat", back_populates="tenancies")
    invoices = relationship("Invoice", back_populates="tenancy", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="tenancy")
    reviews = relationship("Review", back_populates="tenancy")
