"""Property service handling listings, updates, publishing, and ownership checks."""

from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import UserRole
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.property import Property
from app.models.room import Room
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_property(self, owner: User, req: PropertyCreate) -> Property:
        """Create a new property listing."""
        property_obj = Property(
            owner_id=owner.id,
            **req.model_dump()
        )
        self.db.add(property_obj)
        await self.db.flush()
        await self.db.refresh(property_obj)
        return property_obj

    async def get_property_by_id(self, property_id: uuid.UUID) -> Property:
        """Retrieve detailed information about a property."""
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
        return prop

    async def update_property(self, property_id: uuid.UUID, user: User, req: PropertyUpdate) -> Property:
        """Update property details with ownership validation."""
        prop = await self.get_property_by_id(property_id)
        if prop.owner_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this property")

        for field, val in req.model_dump(exclude_unset=True).items():
            setattr(prop, field, val)

        await self.db.flush()
        await self.db.refresh(prop)
        return prop

    async def delete_property(self, property_id: uuid.UUID, user: User) -> bool:
        """Delete property with ownership validation."""
        prop = await self.get_property_by_id(property_id)
        if prop.owner_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this property")

        await self.db.delete(prop)
        await self.db.flush()
        return True

    async def list_owner_properties(self, owner_id: uuid.UUID) -> List[Property]:
        """List all properties owned by a specific owner."""
        query = (
            select(Property)
            .options(
                selectinload(Property.rooms).selectinload(Room.seats),
                selectinload(Property.media),
            )
            .where(Property.owner_id == owner_id)
            .order_by(Property.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def set_publish_status(self, property_id: uuid.UUID, user: User, is_published: bool) -> Property:
        """Toggle property published status."""
        prop = await self.get_property_by_id(property_id)
        if prop.owner_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this property")

        prop.is_published = is_published
        await self.db.flush()
        await self.db.refresh(prop)
        return prop
