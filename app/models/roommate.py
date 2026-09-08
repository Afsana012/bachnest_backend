"""Roommate profile domain model."""

import uuid
from decimal import Decimal
from typing import List
from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Gender, RoommateLookingType, RoommateOccupationCategory
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RoommateProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roommate_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[Gender] = mapped_column(
        SQLEnum(Gender, name="gender_enum", create_type=False),
        nullable=False,
        default=Gender.MALE
    )
    occupation: Mapped[str] = mapped_column(String(255), nullable=False)
    occupation_category: Mapped[RoommateOccupationCategory] = mapped_column(
        SQLEnum(RoommateOccupationCategory, name="roommate_occupation_category_enum"),
        nullable=False,
        default=RoommateOccupationCategory.JOB_HOLDER
    )
    institution_or_company: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    preferred_areas: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    budget_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("5000.00"))
    looking_for: Mapped[RoommateLookingType] = mapped_column(
        SQLEnum(RoommateLookingType, name="roommate_looking_type_enum"),
        nullable=False,
        default=RoommateLookingType.ROOM_WANTED
    )
    move_in_date: Mapped[str] = mapped_column(String(50), nullable=False, default="Immediate")
    lifestyle_tags: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    phone_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="roommate_profile")
