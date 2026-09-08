from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import ParkingRentalPlan, UserRole, VehicleType
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.parking import (
    ParkingBookingCreate,
    ParkingBookingOut,
    ParkingSearchItem,
    ParkingSpaceCreate,
    ParkingSpaceOut,
    ParkingSpaceUpdate,
)
from app.services.parking_service import ParkingService

parking_router = APIRouter(prefix="/parking", tags=["Parking & Garage"])
property_parking_router = APIRouter(prefix="/properties", tags=["Property Parking"])


@parking_router.get("/search", response_model=StandardResponse[List[ParkingSearchItem]])
async def search_parking(
    area: Optional[str] = Query(None),
    vehicle_type: Optional[VehicleType] = Query(None),
    rental_plan: Optional[ParkingRentalPlan] = Query(None),
    max_rate: Optional[Decimal] = Query(None),
    is_covered: Optional[bool] = Query(None),
    has_cctv: Optional[bool] = Query(None),
    only_available: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    items = await service.search_parking_spaces(
        area=area,
        vehicle_type=vehicle_type,
        rental_plan=rental_plan,
        max_rate=max_rate,
        is_covered=is_covered,
        has_cctv=has_cctv,
        only_available=only_available,
        limit=limit,
        offset=offset,
    )
    return StandardResponse(
        success=True,
        message="Available parking spots retrieved successfully",
        data=[ParkingSearchItem.model_validate(it) for it in items],
    )


@property_parking_router.post(
    "/{property_id}/parking",
    response_model=StandardResponse[ParkingSpaceOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))],
)
async def create_parking_space(
    property_id: uuid.UUID,
    req: ParkingSpaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    space = await service.create_parking_space(property_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Parking space created successfully",
        data=ParkingSpaceOut.model_validate(space),
    )


@property_parking_router.get(
    "/{property_id}/parking",
    response_model=StandardResponse[List[ParkingSpaceOut]],
)
async def list_property_parking(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    spaces = await service.list_property_parking(property_id)
    return StandardResponse(
        success=True,
        message="Parking spaces retrieved successfully",
        data=[ParkingSpaceOut.model_validate(s) for s in spaces],
    )


@parking_router.patch(
    "/{parking_id}",
    response_model=StandardResponse[ParkingSpaceOut],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))],
)
async def update_parking_space(
    parking_id: uuid.UUID,
    req: ParkingSpaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    space = await service.update_parking_space(parking_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Parking space updated successfully",
        data=ParkingSpaceOut.model_validate(space),
    )


@parking_router.delete(
    "/{parking_id}",
    response_model=StandardResponse[dict],
    dependencies=[Depends(require_roles([UserRole.OWNER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))],
)
async def delete_parking_space(
    parking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    await service.delete_parking_space(parking_id, current_user)
    return StandardResponse(
        success=True,
        message="Parking space deleted successfully",
        data={"deleted": True},
    )


@parking_router.post(
    "/{parking_id}/book",
    response_model=StandardResponse[ParkingBookingOut],
    status_code=status.HTTP_201_CREATED,
)
async def book_parking(
    parking_id: uuid.UUID,
    req: ParkingBookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    booking = await service.book_parking_space(parking_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Parking space booked successfully",
        data=ParkingBookingOut.model_validate(booking),
    )


@parking_router.get(
    "/me",
    response_model=StandardResponse[List[ParkingBookingOut]],
)
async def get_my_parking_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    bookings = await service.list_user_parking_bookings(current_user.id)
    return StandardResponse(
        success=True,
        message="User parking passes retrieved successfully",
        data=[ParkingBookingOut.model_validate(b) for b in bookings],
    )


@parking_router.post(
    "/bookings/{booking_id}/cancel",
    response_model=StandardResponse[ParkingBookingOut],
)
async def cancel_parking_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ParkingService(db)
    booking = await service.cancel_parking_booking(booking_id, current_user)
    return StandardResponse(
        success=True,
        message="Parking booking cancelled successfully",
        data=ParkingBookingOut.model_validate(booking),
    )
