"""Parking space and parking booking domain models."""

import builtins
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

    @builtins.property
    def active_booking(self) -> Optional["ParkingBooking"]:
        from sqlalchemy import inspect
        if "bookings" in inspect(self).unloaded:
            return None
        if self.bookings:
            for b in self.bookings:
                if b.status == ParkingBookingStatus.ACTIVE:
                    return b
        return None


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

    @builtins.property
    def tenant_name(self) -> Optional[str]:
        from sqlalchemy import inspect
        if "user" in inspect(self).unloaded:
            return None
        return self.user.full_name if self.user else None

    @builtins.property
    def tenant_phone(self) -> Optional[str]:
        from sqlalchemy import inspect
        if "user" in inspect(self).unloaded:
            return None
        return self.user.phone if self.user else None

    @builtins.property
    def tenant_email(self) -> Optional[str]:
        from sqlalchemy import inspect
        if "user" in inspect(self).unloaded:
            return None
        return self.user.email if self.user else None

    @builtins.property
    def space_number_or_name(self) -> Optional[str]:
        from sqlalchemy import inspect
        if "parking_space" in inspect(self).unloaded:
            return None
        return self.parking_space.space_number_or_name if self.parking_space else None

    @builtins.property
    def vehicle_type(self) -> Optional[VehicleType]:
        from sqlalchemy import inspect
        if "parking_space" in inspect(self).unloaded:
            return None
        return self.parking_space.vehicle_type if self.parking_space else None

    @builtins.property
    def property_id(self) -> Optional[uuid.UUID]:
        from sqlalchemy import inspect
        if "parking_space" in inspect(self).unloaded:
            return None
        return self.parking_space.property_id if self.parking_space else None

    @builtins.property
    def property_title(self) -> Optional[str]:
        from sqlalchemy import inspect
        if "parking_space" in inspect(self).unloaded:
            return None
        if self.parking_space and "property" not in inspect(self.parking_space).unloaded:
            return self.parking_space.property.title if self.parking_space.property else None
        return None

    @builtins.property
    def property_address(self) -> Optional[str]:
        from sqlalchemy import inspect
        if "parking_space" in inspect(self).unloaded:
            return None
        if self.parking_space and "property" not in inspect(self.parking_space).unloaded:
            return self.parking_space.property.address_line if self.parking_space.property else None
        return None

