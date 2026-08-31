"""Admin service providing real platform metrics, user moderation, and listing oversight."""

from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ComplaintStatus, TenancyStatus
from app.core.exceptions import ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.complaint import Complaint
from app.models.emergency import AuditLog, EmergencyAlert
from app.models.property import Property
from app.models.room import Room
from app.models.user import User


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(self) -> dict:
        """Compute real aggregated platform metrics."""
        total_users = (await self.db.execute(select(func.count(User.id)))).scalar_one()
        verified_properties = (
            await self.db.execute(select(func.count(Property.id)).where(Property.is_verified_by_admin == True))
        ).scalar_one()
        active_tenancies = (
            await self.db.execute(select(func.count(Tenancy.id)).where(Tenancy.status == TenancyStatus.ACTIVE))
        ).scalar_one()
        open_complaints = (
            await self.db.execute(select(func.count(Complaint.id)).where(Complaint.status == ComplaintStatus.OPEN))
        ).scalar_one()
        active_sos = (
            await self.db.execute(select(func.count(EmergencyAlert.id)).where(EmergencyAlert.is_active == True))
        ).scalar_one()

        return {
            "total_users": total_users,
            "verified_properties": verified_properties,
            "active_tenancies": active_tenancies,
            "open_complaints": open_complaints,
            "active_sos": active_sos,
        }

    async def list_users(self, page: int = 1, limit: int = 20) -> List[User]:
        """List platform users with pagination."""
        query = select(User).order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def set_user_status(self, user_id: uuid.UUID, is_active: bool) -> User:
        """Activate or deactivate a user account."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise ResourceNotFoundError(message="User not found")

        user.is_active = is_active
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_pending_properties(self) -> List[Property]:
        """List properties awaiting admin verification."""
        query = (
            select(Property)
            .options(
                selectinload(Property.rooms).selectinload(Room.seats),
                selectinload(Property.media),
            )
            .where(Property.is_verified_by_admin == False)
            .order_by(Property.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def verify_property(self, property_id: uuid.UUID, is_verified: bool) -> Property:
        """Admin verifies or rejects a property listing."""
        query = (
            select(Property)
            .options(
                selectinload(Property.rooms).selectinload(Room.seats),
                selectinload(Property.media),
            )
            .where(Property.id == property_id)
        )
        result = await self.db.execute(query)
        prop = result.scalar_one_or_none()
        if not prop:
            raise ResourceNotFoundError(message="Property not found")

        prop.is_verified_by_admin = is_verified
        await self.db.flush()
        await self.db.refresh(prop)
        return prop
