"""Room, RoomSeat, and PropertyMedia models."""

import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RoomType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Room(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rooms"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    room_number_or_name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_type: Mapped[RoomType] = mapped_column(
        SQLEnum(RoomType, name="room_type_enum"),
        default=RoomType.SINGLE,
        nullable=False
    )
    
    # Financials (BDT)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    security_deposit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    
    # Features
    has_attached_bathroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_balcony: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_ac: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_furnished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Capacity
    total_capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    property = relationship("Property", back_populates="rooms")
    seats = relationship("RoomSeat", back_populates="room", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="room")
    tenancies = relationship("Tenancy", back_populates="room")


class RoomSeat(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "room_seats"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    seat_identifier: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Seat A", "Bed 1"
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    room = relationship("Room", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat")
    tenancies = relationship("Tenancy", back_populates="seat")


class PropertyMedia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "property_media"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    media_url: Mapped[str] = mapped_column(String(512), nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), default="IMAGE", nullable=False)  # IMAGE, VIDEO, 360_TOUR
    caption: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    property = relationship("Property", back_populates="media")
