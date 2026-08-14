"""Booking and Tenancy API endpoints."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import BookingStatus, TenancyStatus, UserRole
from app.core.exceptions import InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Booking, Tenancy
from app.models.property import Property
from app.models.room import Room
from app.models.user import User
from app.schemas.booking import BookingCreateRequest, BookingDecisionRequest, BookingOut, TenancyOut
from app.schemas.common import StandardResponse

bookings_router = APIRouter(prefix="/bookings", tags=["Bookings"])
tenancies_router = APIRouter(prefix="/tenancies", tags=["Tenancies"])


@bookings_router.post("/request", response_model=StandardResponse[BookingOut], status_code=status.HTTP_201_CREATED)
async def create_booking_request(
    req: BookingCreateRequest,
    current_user: User = Depends(require_roles(UserRole.BACHELOR)),
    db: AsyncSession = Depends(get_db)
):
    """Submit a room/seat rental booking request."""
    # Verify room exists and is available
    room_query = select(Room).where(Room.id == req.room_id, Room.property_id == req.property_id)
    room = (await db.execute(room_query)).scalar_one_or_none()
    if not room or not room.is_available:
        raise InvalidBookingError(message="Selected room is not available for booking")

    booking = Booking(
        tenant_id=current_user.id,
        property_id=req.property_id,
        room_id=req.room_id,
        seat_id=req.seat_id,
        requested_move_in_date=req.requested_move_in_date,
        token_deposit_amount=req.token_deposit_amount,
        booking_status=BookingStatus.REQUESTED,
    )
    db.add(booking)
    await db.flush()
    await db.refresh(booking)

    return StandardResponse(
        success=True,
        message="Booking request submitted to owner",
        data=BookingOut.model_validate(booking)
    )


@bookings_router.get("/me", response_model=StandardResponse[List[BookingOut]])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List bookings belonging to the current user."""
    query = select(Booking).where(Booking.tenant_id == current_user.id)
    result = await db.execute(query)
    bookings = result.scalars().all()
    return StandardResponse(
        success=True,
        message="Bookings retrieved",
        data=[BookingOut.model_validate(b) for b in bookings]
    )


@bookings_router.patch("/{booking_id}/decision", response_model=StandardResponse[BookingOut])
async def owner_booking_decision(
    booking_id: uuid.UUID,
    req: BookingDecisionRequest,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db)
):
    """Owner approves or rejects a booking request."""
    query = select(Booking).where(Booking.id == booking_id)
    booking = (await db.execute(query)).scalar_one_or_none()
    if not booking:
        raise ResourceNotFoundError(message="Booking request not found")

    prop_query = select(Property).where(Property.id == booking.property_id)
    prop = (await db.execute(prop_query)).scalar_one_or_none()
    if not prop or prop.owner_id != current_user.id:
        raise PermissionDeniedError(message="You do not own the property for this booking")

    if req.decision == "APPROVE":
        booking.booking_status = BookingStatus.APPROVED_BY_OWNER
        # Create Tenancy automatically upon approval
        room_query = select(Room).where(Room.id == booking.room_id)
        room = (await db.execute(room_query)).scalar_one_or_none()
        
        tenancy = Tenancy(
            booking_id=booking.id,
            tenant_id=booking.tenant_id,
            owner_id=current_user.id,
            property_id=booking.property_id,
            room_id=booking.room_id,
            seat_id=booking.seat_id,
            agreed_monthly_rent=room.monthly_rent if room else 0,
            agreed_security_deposit=room.security_deposit if room else 0,
            lease_start_date=booking.requested_move_in_date,
            status=TenancyStatus.ACTIVE,
        )
        db.add(tenancy)
    else:
        booking.booking_status = BookingStatus.REJECTED
        booking.cancellation_reason = req.reason

    await db.flush()
    await db.refresh(booking)
    return StandardResponse(
        success=True,
        message=f"Booking request {booking.booking_status.value}",
        data=BookingOut.model_validate(booking)
    )


# --- TENANCY ENDPOINTS ---
@tenancies_router.get("/me", response_model=StandardResponse[List[TenancyOut]])
async def get_my_tenancies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve active or past tenancies for tenant or owner."""
    if current_user.role == UserRole.OWNER:
        query = select(Tenancy).where(Tenancy.owner_id == current_user.id)
    else:
        query = select(Tenancy).where(Tenancy.tenant_id == current_user.id)
    result = await db.execute(query)
    tenancies = result.scalars().all()
    return StandardResponse(
        success=True,
        message="Tenancies retrieved",
        data=[TenancyOut.model_validate(t) for t in tenancies]
    )
