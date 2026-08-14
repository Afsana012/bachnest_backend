"""Property domain model with geospatial support."""

import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Enum as SQLEnum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PropertyType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Property(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "properties"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(
        SQLEnum(PropertyType, name="property_type_enum"),
        default=PropertyType.FLAT,
        nullable=False
    )
    
    # Address & Coordinates
    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    area_neighborhood: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), default="Dhaka", nullable=False, index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Property Specifications & Amenities
    total_floors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    floor_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    flat_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    has_lift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_generator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_cctv: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gate_closing_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "11:00 PM"
    visitor_policy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Publication & Verification status
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_verified_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    verified_at: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="properties")
    rooms = relationship("Room", back_populates="property", cascade="all, delete-orphan")
    media = relationship("PropertyMedia", back_populates="property", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="property")
    tenancies = relationship("Tenancy", back_populates="property")
    complaints = relationship("Complaint", back_populates="property")
    notices = relationship("Notice", back_populates="property", cascade="all, delete-orphan")
