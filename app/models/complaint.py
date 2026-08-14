"""Complaint and Notice domain models."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ComplaintCategory, ComplaintPriority, ComplaintStatus, NoticePriority
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaints"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    room_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True
    )
    tenancy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenancies.id", ondelete="SET NULL"),
        nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ComplaintCategory] = mapped_column(
        SQLEnum(ComplaintCategory, name="complaint_category_enum"),
        default=ComplaintCategory.OTHER,
        nullable=False
    )
    priority: Mapped[ComplaintPriority] = mapped_column(
        SQLEnum(ComplaintPriority, name="complaint_priority_enum"),
        default=ComplaintPriority.MEDIUM,
        nullable=False
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus, name="complaint_status_enum"),
        default=ComplaintStatus.OPEN,
        nullable=False,
        index=True
    )
    
    sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_urls: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list, nullable=True)
    repair_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    cost_bearer: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # OWNER, TENANT, SHARED
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    property = relationship("Property", back_populates="complaints")
    tenancy = relationship("Tenancy", back_populates="complaints")


class Notice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notices"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[NoticePriority] = mapped_column(
        SQLEnum(NoticePriority, name="notice_priority_enum"),
        default=NoticePriority.NORMAL,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    property = relationship("Property", back_populates="notices")
    read_receipts = relationship("NoticeRead", back_populates="notice", cascade="all, delete-orphan")


class NoticeRead(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notice_reads"

    notice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    notice = relationship("Notice", back_populates="read_receipts")
