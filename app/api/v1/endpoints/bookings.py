"""Booking and Tenancy API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.booking import (
    BookingCreateRequest,
    BookingDecisionRequest,
    BookingOut,
    TenancyNoticeRequest,
    TenancyOut,
)
from app.schemas.common import StandardResponse
from app.services.booking_service import BookingService
from app.services.tenancy_service import TenancyService

bookings_router = APIRouter(prefix="/bookings", tags=["Bookings"])
tenancies_router = APIRouter(prefix="/tenancies", tags=["Tenancies"])


# --- BOOKINGS ---
@bookings_router.post("/request", response_model=StandardResponse[BookingOut], status_code=status.HTTP_201_CREATED)
async def create_booking_request(
    req: BookingCreateRequest,
    current_user: User = Depends(require_roles(UserRole.BACHELOR)),
    db: AsyncSession = Depends(get_db),
):
    """Submit a room/seat rental booking request."""
    booking_service = BookingService(db)
    booking = await booking_service.create_booking_request(current_user, req)
    return StandardResponse(
        success=True,
        message="Booking request submitted to owner",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.get("/me", response_model=StandardResponse[List[BookingOut]])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List bookings belonging to the current tenant or owner's properties."""
    booking_service = BookingService(db)
    bookings = await booking_service.list_user_bookings(current_user)
    return StandardResponse(
        success=True,
        message="Bookings retrieved",
        data=[BookingOut.model_validate(b) for b in bookings],
    )


@bookings_router.get("/{booking_id}", response_model=StandardResponse[BookingOut])
async def get_booking_by_id(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information about a specific booking."""
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id(booking_id, current_user)
    return StandardResponse(
        success=True,
        message="Booking details retrieved",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.patch("/{booking_id}/decision", response_model=StandardResponse[BookingOut])
async def owner_booking_decision(
    booking_id: uuid.UUID,
    req: BookingDecisionRequest,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Owner approves or rejects a booking request."""
    booking_service = BookingService(db)
    booking = await booking_service.owner_decision(booking_id, current_user, req)
    return StandardResponse(
        success=True,
        message=f"Booking request {booking.booking_status.value.lower()}",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.post("/{booking_id}/cancel", response_model=StandardResponse[BookingOut])
async def cancel_booking(
    booking_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending booking request."""
    booking_service = BookingService(db)
    booking = await booking_service.cancel_booking(booking_id, current_user, reason)
    return StandardResponse(
        success=True,
        message="Booking request cancelled",
        data=BookingOut.model_validate(booking),
    )


# --- TENANCIES ---
@tenancies_router.get("/me", response_model=StandardResponse[List[TenancyOut]])
async def get_my_tenancies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve active or past tenancies for tenant or owner."""
    tenancy_service = TenancyService(db)
    tenancies = await tenancy_service.list_user_tenancies(current_user)
    return StandardResponse(
        success=True,
        message="Tenancies retrieved",
        data=[TenancyOut.model_validate(t) for t in tenancies],
    )


@tenancies_router.get("/{tenancy_id}", response_model=StandardResponse[TenancyOut])
async def get_tenancy_by_id(
    tenancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve specific tenancy agreement details."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.get_tenancy_by_id(tenancy_id, current_user)
    return StandardResponse(
        success=True,
        message="Tenancy details retrieved",
        data=TenancyOut.model_validate(tenancy),
    )


@tenancies_router.patch("/{tenancy_id}/notice", response_model=StandardResponse[TenancyOut])
async def serve_tenancy_notice(
    tenancy_id: uuid.UUID,
    req: TenancyNoticeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve a move-out notice on an active tenancy."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.serve_notice(tenancy_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Move-out notice served successfully",
        data=TenancyOut.model_validate(tenancy),
    )


@tenancies_router.patch("/{tenancy_id}/terminate", response_model=StandardResponse[TenancyOut])
async def terminate_tenancy(
    tenancy_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Terminate tenancy and restore room/seat inventory availability."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.terminate_tenancy(tenancy_id, current_user)
    return StandardResponse(
        success=True,
        message="Tenancy terminated and inventory released",
        data=TenancyOut.model_validate(tenancy),
    )
