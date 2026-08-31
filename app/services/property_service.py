"""Property service handling listings, updates, publishing, and ownership checks."""

from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import UserRole
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.property import Property
from app.models.room import PropertyMedia, Room
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyMediaCreate, PropertyUpdate


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
        return await self.get_property_by_id(property_obj.id)

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

    async def add_media(self, property_id: uuid.UUID, user: User, items: List[PropertyMediaCreate]) -> Property:
        """Attach uploaded media to a property with ownership validation."""
        prop = await self.get_property_by_id(property_id)
        if prop.owner_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this property")

        cover_exists = any(m.is_cover for m in prop.media)
        incoming_has_cover = any(item.is_cover for item in items)
        for index, item in enumerate(items):
            is_cover = item.is_cover
            if not cover_exists and not incoming_has_cover and index == 0:
                is_cover = True
            self.db.add(PropertyMedia(
                property_id=property_id,
                media_url=item.media_url,
                media_type=item.media_type,
                caption=item.caption,
                is_cover=is_cover,
                display_order=item.display_order,
            ))
        await self.db.flush()
        return await self.get_property_by_id(property_id)

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

    async def list_public_properties(self, page: int = 1, size: int = 20) -> List[Property]:
        """List published properties for public browsing."""
        query = (
            select(Property)
            .options(
                selectinload(Property.rooms).selectinload(Room.seats),
                selectinload(Property.media),
            )
            .where(Property.is_published == True)
            .order_by(Property.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

