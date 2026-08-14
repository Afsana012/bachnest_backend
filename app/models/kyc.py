"""KYC, Roommate Preferences, and Emergency Contact models."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import KYCDocumentType, KYCStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserKYC(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_kyc"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    status: Mapped[KYCStatus] = mapped_column(
        SQLEnum(KYCStatus, name="kyc_status_enum"),
        default=KYCStatus.UNVERIFIED,
        nullable=False,
        index=True
    )
    document_type: Mapped[KYCDocumentType] = mapped_column(
        SQLEnum(KYCDocumentType, name="kyc_document_type_enum"),
        nullable=False
    )
    document_number: Mapped[str] = mapped_column(String(100), nullable=False)
    front_document_url: Mapped[str] = mapped_column(String(512), nullable=False)
    back_document_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    student_or_work_id_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    raw_verification_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="kyc", foreign_keys=[user_id])


class RoommatePreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roommate_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    smoking_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sleep_schedule: Mapped[str] = mapped_column(String(50), default="NORMAL", nullable=False)  # EARLY_BIRD, NIGHT_OWL, FLEXIBLE
    cleanliness_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1 to 5
    guests_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dietary_preference: Mapped[str] = mapped_column(String(50), default="ANY", nullable=False)  # VEG, NON_VEG, ANY
    study_habit: Mapped[str] = mapped_column(String(50), default="QUIET", nullable=False)
    additional_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="roommate_preference")


class EmergencyContact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_contacts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PARENT, SIBLING, FRIEND, RELATIVE
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="emergency_contacts")
