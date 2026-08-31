"""User domain model."""

from typing import List, Optional
from sqlalchemy import Boolean, Enum as SQLEnum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Gender, UserRole
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum"),
        default=UserRole.BACHELOR,
        nullable=False,
        index=True
    )
    gender: Mapped[Gender] = mapped_column(
        SQLEnum(Gender, name="gender_enum"),
        default=Gender.OTHER,
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    institution_or_company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    # Relationships
    kyc = relationship("UserKYC", back_populates="user", uselist=False, foreign_keys="[UserKYC.user_id]", cascade="all, delete-orphan")
    roommate_preference = relationship("RoommatePreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tenant", foreign_keys="[Booking.tenant_id]", cascade="all, delete-orphan")
    tenancies_as_tenant = relationship("Tenancy", back_populates="tenant", foreign_keys="[Tenancy.tenant_id]")
    tenancies_as_owner = relationship("Tenancy", back_populates="owner", foreign_keys="[Tenancy.owner_id]")
