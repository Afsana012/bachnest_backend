"""Tenancy service managing active rental agreements, notice periods, and move-outs."""

from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import AgreementStatus, TenancyStatus, UserRole
from app.core.exceptions import InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.room import Room, RoomSeat
from app.models.user import User
from app.schemas.booking import TenancyNoticeRequest


class TenancyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_user_tenancies(self, user: User) -> List[Tenancy]:
        """List tenancies for tenant or owner."""
        if user.role == UserRole.OWNER:
            query = select(Tenancy).where(Tenancy.owner_id == user.id).order_by(Tenancy.created_at.desc())
        elif user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            query = select(Tenancy).order_by(Tenancy.created_at.desc())
        else:
            query = select(Tenancy).where(Tenancy.tenant_id == user.id).order_by(Tenancy.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tenancy_by_id(self, tenancy_id: uuid.UUID, user: User) -> Tenancy:
        """Retrieve tenancy details with authorization checks."""
        query = select(Tenancy).where(Tenancy.id == tenancy_id)
        result = await self.db.execute(query)
        tenancy = result.scalar_one_or_none()
        if not tenancy:
            raise ResourceNotFoundError(message="Tenancy not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            if tenancy.tenant_id != user.id and tenancy.owner_id != user.id:
                raise PermissionDeniedError(message="You do not have access to this tenancy agreement")

        return tenancy

    async def serve_notice(self, tenancy_id: uuid.UUID, user: User, req: TenancyNoticeRequest) -> Tenancy:
        """Tenant or Owner serves formal move-out notice."""
        tenancy = await self.get_tenancy_by_id(tenancy_id, user)
        if tenancy.status != TenancyStatus.ACTIVE:
            raise InvalidBookingError(message=f"Notice cannot be served on tenancy in status {tenancy.status.value}")

        tenancy.status = TenancyStatus.NOTICE_SERVED
        tenancy.lease_end_date = req.move_out_date

        await self.db.flush()
        await self.db.refresh(tenancy)
        return tenancy

    async def terminate_tenancy(self, tenancy_id: uuid.UUID, user: User) -> Tenancy:
        """Complete move-out and release room/seat inventory."""
        tenancy = await self.get_tenancy_by_id(tenancy_id, user)
        if tenancy.status in (TenancyStatus.TERMINATED, TenancyStatus.EVICTED):
            raise InvalidBookingError(message="Tenancy is already terminated")

        tenancy.status = TenancyStatus.TERMINATED
        tenancy.agreement_status = AgreementStatus.EXPIRED

        # Release seat if occupied
        if tenancy.seat_id:
            seat_query = select(RoomSeat).where(RoomSeat.id == tenancy.seat_id).with_for_update()
            seat = (await self.db.execute(seat_query)).scalar_one_or_none()
            if seat:
                seat.is_occupied = False

        # Decrement room occupancy
        if tenancy.room_id:
            room_query = select(Room).where(Room.id == tenancy.room_id).with_for_update()
            room = (await self.db.execute(room_query)).scalar_one_or_none()
            if room:
                room.current_occupancy = max(0, room.current_occupancy - 1)
                room.is_available = True

        await self.db.flush()
        await self.db.refresh(tenancy)
        return tenancy
