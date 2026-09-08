"""Parking space and parking booking domain models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import Boolean, Date, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ParkingBookingStatus, ParkingRentalPlan, VehicleType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ParkingSpace(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "parking_spaces"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    space_number_or_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SQLEnum(VehicleType, name="vehicle_type_enum"),
        default=VehicleType.BIKE,
        nullable=False,
        index=True
    )
    
    monthly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    daily_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    is_covered: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_cctv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    property = relationship("Property", back_populates="parking_spaces")
    bookings = relationship("ParkingBooking", back_populates="parking_space", cascade="all, delete-orphan")


class ParkingBooking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "parking_bookings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parking_space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parking_spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    rental_plan: Mapped[ParkingRentalPlan] = mapped_column(
        SQLEnum(ParkingRentalPlan, name="parking_rental_plan_enum"),
        default=ParkingRentalPlan.MONTHLY,
        nullable=False
    )
    vehicle_registration_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    status: Mapped[ParkingBookingStatus] = mapped_column(
        SQLEnum(ParkingBookingStatus, name="parking_booking_status_enum"),
        default=ParkingBookingStatus.ACTIVE,
        nullable=False,
        index=True
    )

    # Relationships
    user = relationship("User", back_populates="parking_bookings")
    parking_space = relationship("ParkingSpace", back_populates="bookings")
