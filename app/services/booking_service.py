"""Booking service managing booking requests, concurrency-safe approvals, and rejections."""

from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AgreementStatus, BookingStatus, TenancyStatus, UserRole
from app.core.exceptions import ConflictError, InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Booking, Tenancy
from app.models.property import Property
from app.models.room import Room, RoomSeat
from app.models.user import User
from app.schemas.booking import BookingCreateRequest, BookingDecisionRequest


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_booking_request(self, tenant: User, req: BookingCreateRequest) -> Booking:
        """Submit a booking request with concurrency protection."""
        # 1. Verify Property
        prop_query = select(Property).where(Property.id == req.property_id)
        prop = (await self.db.execute(prop_query)).scalar_one_or_none()
        if not prop:
            raise ResourceNotFoundError(message="Property not found")
        if not prop.is_published:
            raise InvalidBookingError(message="Property is not currently available for booking")

        # 2. Lock Room with row-level lock
        room_query = (
            select(Room)
            .where(Room.id == req.room_id, Room.property_id == req.property_id)
            .with_for_update()
        )
        room = (await self.db.execute(room_query)).scalar_one_or_none()
        if not room or not room.is_available:
            raise InvalidBookingError(message="Selected room is not available for booking")

        # 3. If Seat specified, lock Seat
        if req.seat_id:
            seat_query = (
                select(RoomSeat)
                .where(RoomSeat.id == req.seat_id, RoomSeat.room_id == req.room_id)
                .with_for_update()
            )
            seat = (await self.db.execute(seat_query)).scalar_one_or_none()
            if not seat:
                raise ResourceNotFoundError(message="Specified seat not found in this room")
            if seat.is_occupied:
                raise ConflictError(message="Selected seat is already occupied")

        # 4. Check for duplicate pending booking by same user for same room
        dup_query = select(Booking).where(
            Booking.tenant_id == tenant.id,
            Booking.room_id == req.room_id,
            Booking.booking_status == BookingStatus.REQUESTED
        )
        existing_booking = (await self.db.execute(dup_query)).scalar_one_or_none()
        if existing_booking:
            raise ConflictError(message="You already have a pending booking request for this room")

        booking = Booking(
            tenant_id=tenant.id,
            property_id=req.property_id,
            room_id=req.room_id,
            seat_id=req.seat_id,
            requested_move_in_date=req.requested_move_in_date,
            token_deposit_amount=req.token_deposit_amount,
            booking_status=BookingStatus.REQUESTED,
        )
        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def get_booking_by_id(self, booking_id: uuid.UUID, user: User) -> Booking:
        """Retrieve booking by ID with authorization checks."""
        query = select(Booking).where(Booking.id == booking_id)
        booking = (await self.db.execute(query)).scalar_one_or_none()
        if not booking:
            raise ResourceNotFoundError(message="Booking not found")

        if user.role != UserRole.SUPER_ADMIN and user.role != UserRole.ADMIN:
            if booking.tenant_id != user.id:
                # Check if user is the owner of the property
                prop_query = select(Property).where(Property.id == booking.property_id)
                prop = (await self.db.execute(prop_query)).scalar_one_or_none()
                if not prop or prop.owner_id != user.id:
                    raise PermissionDeniedError(message="You do not have permission to view this booking")

        return booking

    async def list_user_bookings(self, user: User) -> List[Booking]:
        """List bookings for tenant or owner."""
        if user.role == UserRole.OWNER:
            query = (
                select(Booking)
                .join(Property, Property.id == Booking.property_id)
                .where(Property.owner_id == user.id)
                .order_by(Booking.created_at.desc())
            )
        else:
            query = select(Booking).where(Booking.tenant_id == user.id).order_by(Booking.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancel_booking(self, booking_id: uuid.UUID, user: User, reason: Optional[str] = None) -> Booking:
        """Cancel an open booking request."""
        booking = await self.get_booking_by_id(booking_id, user)
        if booking.booking_status != BookingStatus.REQUESTED:
            raise InvalidBookingError(message=f"Cannot cancel a booking in status {booking.booking_status.value}")

        booking.booking_status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason or "Cancelled by user"

        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def owner_decision(self, booking_id: uuid.UUID, owner: User, req: BookingDecisionRequest) -> Booking:
        """Owner approves or rejects booking, creating Tenancy atomically on approval."""
        query = select(Booking).where(Booking.id == booking_id).with_for_update()
        booking = (await self.db.execute(query)).scalar_one_or_none()
        if not booking:
            raise ResourceNotFoundError(message="Booking request not found")

        prop_query = select(Property).where(Property.id == booking.property_id)
        prop = (await self.db.execute(prop_query)).scalar_one_or_none()
        if not prop or (prop.owner_id != owner.id and owner.role != UserRole.SUPER_ADMIN):
            raise PermissionDeniedError(message="You do not own the property for this booking")

        if booking.booking_status != BookingStatus.REQUESTED:
            raise InvalidBookingError(message=f"Booking is already in status {booking.booking_status.value}")

        if req.decision.upper() == "APPROVE":
            # Lock room
            room_query = select(Room).where(Room.id == booking.room_id).with_for_update()
            room = (await self.db.execute(room_query)).scalar_one_or_none()
            if not room:
                raise ResourceNotFoundError(message="Room not found")

            # Check seat if seat_id provided
            if booking.seat_id:
                seat_query = select(RoomSeat).where(RoomSeat.id == booking.seat_id).with_for_update()
                seat = (await self.db.execute(seat_query)).scalar_one_or_none()
                if not seat or seat.is_occupied:
                    raise ConflictError(message="Seat is already occupied or unavailable")
                seat.is_occupied = True
                agreed_rent = seat.monthly_rent
            else:
                agreed_rent = room.monthly_rent

            # Update room occupancy
            room.current_occupancy += 1
            if room.current_occupancy >= room.total_capacity:
                room.is_available = False

            booking.booking_status = BookingStatus.APPROVED_BY_OWNER
            booking.owner_remarks = req.reason

            # Create Active Tenancy
            tenancy = Tenancy(
                booking_id=booking.id,
                tenant_id=booking.tenant_id,
                owner_id=prop.owner_id,
                property_id=booking.property_id,
                room_id=booking.room_id,
                seat_id=booking.seat_id,
                agreed_monthly_rent=agreed_rent,
                agreed_security_deposit=room.security_deposit,
                lease_start_date=booking.requested_move_in_date,
                notice_period_days=30,
                status=TenancyStatus.ACTIVE,
                agreement_status=AgreementStatus.PENDING_SIGNATURE,
            )
            self.db.add(tenancy)

        else:
            booking.booking_status = BookingStatus.REJECTED
            booking.cancellation_reason = req.reason or "Rejected by property owner"

        await self.db.flush()
        await self.db.refresh(booking)
        return booking
