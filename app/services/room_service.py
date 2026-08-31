"""Room and Seat service managing inventory, capacity, and seat occupancy."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import UserRole
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.property import Property
from app.models.room import Room, RoomSeat
from app.models.user import User
from app.schemas.property import RoomCreate, RoomSeatCreate, RoomUpdate


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_property_ownership(self, property_id: uuid.UUID, user: User) -> Property:
        query = select(Property).where(Property.id == property_id)
        result = await self.db.execute(query)
        prop = result.scalar_one_or_none()
        if not prop:
            raise ResourceNotFoundError(message="Property not found")
        if prop.owner_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this property")
        return prop

    async def create_room(self, property_id: uuid.UUID, user: User, req: RoomCreate) -> Room:
        """Create a room under a property."""
        await self._verify_property_ownership(property_id, user)

        room = Room(
            property_id=property_id,
            **req.model_dump()
        )
        self.db.add(room)
        await self.db.flush()
        return await self.get_room_by_id(room.id)

    async def list_rooms(self, property_id: uuid.UUID) -> List[Room]:
        """List all rooms for a property."""
        query = (
            select(Room)
            .options(selectinload(Room.seats))
            .where(Room.property_id == property_id)
            .order_by(Room.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_room_by_id(self, room_id: uuid.UUID) -> Room:
        """Retrieve room details by ID."""
        query = (
            select(Room)
            .options(selectinload(Room.seats))
            .where(Room.id == room_id)
        )
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()
        if not room:
            raise ResourceNotFoundError(message="Room not found")
        return room

    async def update_room(self, room_id: uuid.UUID, user: User, req: RoomUpdate) -> Room:
        """Update room details."""
        room = await self.get_room_by_id(room_id)
        await self._verify_property_ownership(room.property_id, user)

        for field, val in req.model_dump(exclude_unset=True).items():
            setattr(room, field, val)

        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def delete_room(self, room_id: uuid.UUID, user: User) -> bool:
        """Delete room."""
        room = await self.get_room_by_id(room_id)
        await self._verify_property_ownership(room.property_id, user)

        await self.db.delete(room)
        await self.db.flush()
        return True

    # --- SEATS ---
    async def create_seat(self, room_id: uuid.UUID, user: User, req: RoomSeatCreate) -> RoomSeat:
        """Add a seat to a shared room."""
        room = await self.get_room_by_id(room_id)
        await self._verify_property_ownership(room.property_id, user)

        seat = RoomSeat(
            room_id=room_id,
            seat_identifier=req.seat_identifier,
            monthly_rent=req.monthly_rent,
            is_occupied=False,
        )
        self.db.add(seat)
        await self.db.flush()
        await self.db.refresh(seat)
        return seat

    async def list_seats(self, room_id: uuid.UUID) -> List[RoomSeat]:
        """List seats in a room."""
        query = select(RoomSeat).where(RoomSeat.room_id == room_id).order_by(RoomSeat.seat_identifier.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_seat(self, seat_id: uuid.UUID, user: User, req: RoomSeatCreate) -> RoomSeat:
        """Update seat rent or identifier."""
        query = select(RoomSeat).where(RoomSeat.id == seat_id)
        result = await self.db.execute(query)
        seat = result.scalar_one_or_none()
        if not seat:
            raise ResourceNotFoundError(message="Seat not found")

        room = await self.get_room_by_id(seat.room_id)
        await self._verify_property_ownership(room.property_id, user)

        seat.seat_identifier = req.seat_identifier
        seat.monthly_rent = req.monthly_rent

        await self.db.flush()
        await self.db.refresh(seat)
        return seat

    async def delete_seat(self, seat_id: uuid.UUID, user: User) -> bool:
        """Delete a seat."""
        query = select(RoomSeat).where(RoomSeat.id == seat_id)
        result = await self.db.execute(query)
        seat = result.scalar_one_or_none()
        if not seat:
            raise ResourceNotFoundError(message="Seat not found")

        room = await self.get_room_by_id(seat.room_id)
        await self._verify_property_ownership(room.property_id, user)

        await self.db.delete(seat)
        await self.db.flush()
        return True
