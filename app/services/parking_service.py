from datetime import date
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ParkingBookingStatus, ParkingRentalPlan, UserRole, VehicleType
from app.core.exceptions import BadRequestError, PermissionDeniedError, ResourceNotFoundError
from app.models.parking import ParkingBooking, ParkingSpace
from app.models.property import Property
from app.models.user import User
from app.schemas.parking import ParkingBookingCreate, ParkingSpaceCreate, ParkingSpaceUpdate


class ParkingService:
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

    async def create_parking_space(
        self, property_id: uuid.UUID, user: User, req: ParkingSpaceCreate
    ) -> ParkingSpace:
        await self._verify_property_ownership(property_id, user)
        space = ParkingSpace(
            property_id=property_id,
            **req.model_dump()
        )
        self.db.add(space)
        await self.db.flush()
        await self.db.refresh(space)
        return space

    async def update_parking_space(
        self, parking_id: uuid.UUID, user: User, req: ParkingSpaceUpdate
    ) -> ParkingSpace:
        query = select(ParkingSpace).where(ParkingSpace.id == parking_id)
        result = await self.db.execute(query)
        space = result.scalar_one_or_none()
        if not space:
            raise ResourceNotFoundError(message="Parking space not found")

        await self._verify_property_ownership(space.property_id, user)

        update_data = req.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(space, field, value)

        await self.db.flush()
        await self.db.refresh(space)
        return space

    async def delete_parking_space(self, parking_id: uuid.UUID, user: User) -> bool:
        query = select(ParkingSpace).where(ParkingSpace.id == parking_id)
        result = await self.db.execute(query)
        space = result.scalar_one_or_none()
        if not space:
            raise ResourceNotFoundError(message="Parking space not found")

        await self._verify_property_ownership(space.property_id, user)
        await self.db.delete(space)
        await self.db.flush()
        return True

    async def list_property_parking(self, property_id: uuid.UUID) -> List[ParkingSpace]:
        query = (
            select(ParkingSpace)
            .where(ParkingSpace.property_id == property_id)
            .order_by(ParkingSpace.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_parking_spaces(
        self,
        area: Optional[str] = None,
        vehicle_type: Optional[VehicleType] = None,
        rental_plan: Optional[ParkingRentalPlan] = None,
        max_rate: Optional[Decimal] = None,
        is_covered: Optional[bool] = None,
        has_cctv: Optional[bool] = None,
        only_available: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        query = (
            select(ParkingSpace, Property, User)
            .join(Property, ParkingSpace.property_id == Property.id)
            .join(User, Property.owner_id == User.id)
            .where(Property.is_published == True)
        )

        if only_available:
            query = query.where(ParkingSpace.is_available == True)

        if area:
            query = query.where(Property.area_neighborhood.ilike(f"%{area}%"))

        if vehicle_type:
            query = query.where(ParkingSpace.vehicle_type == vehicle_type)

        if is_covered is not None:
            query = query.where(ParkingSpace.is_covered == is_covered)

        if has_cctv is not None:
            query = query.where(ParkingSpace.has_cctv == has_cctv)

        if max_rate is not None:
            if rental_plan == ParkingRentalPlan.DAILY:
                query = query.where(ParkingSpace.daily_rate <= max_rate)
            else:
                query = query.where(ParkingSpace.monthly_rate <= max_rate)

        query = query.order_by(ParkingSpace.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for space, prop, owner in rows:
            items.append({
                "id": space.id,
                "property_id": prop.id,
                "property_title": prop.title,
                "property_address": prop.address_line,
                "area_neighborhood": prop.area_neighborhood,
                "city": prop.city,
                "space_number_or_name": space.space_number_or_name,
                "vehicle_type": space.vehicle_type,
                "monthly_rate": space.monthly_rate,
                "daily_rate": space.daily_rate,
                "is_covered": space.is_covered,
                "has_cctv": space.has_cctv,
                "is_available": space.is_available,
                "owner_name": owner.full_name,
                "owner_phone": owner.phone,
            })
        return items

    async def book_parking_space(
        self, parking_id: uuid.UUID, user: User, req: ParkingBookingCreate
    ) -> ParkingBooking:
        query = (
            select(ParkingSpace)
            .where(ParkingSpace.id == parking_id)
            .with_for_update()
        )
        result = await self.db.execute(query)
        space = result.scalar_one_or_none()
        if not space:
            raise ResourceNotFoundError(message="Parking space not found")

        if not space.is_available:
            raise BadRequestError(message="This parking space is currently occupied or unavailable")

        if req.rental_plan == ParkingRentalPlan.DAILY:
            if not space.daily_rate:
                raise BadRequestError(message="Daily rental is not offered for this space")
            if req.end_date and req.end_date > req.start_date:
                days = (req.end_date - req.start_date).days
                total_amount = space.daily_rate * Decimal(max(1, days))
            else:
                total_amount = space.daily_rate
        else:
            total_amount = space.monthly_rate

        booking = ParkingBooking(
            user_id=user.id,
            parking_space_id=space.id,
            rental_plan=req.rental_plan,
            vehicle_registration_number=req.vehicle_registration_number.strip().upper(),
            start_date=req.start_date,
            end_date=req.end_date,
            total_amount=total_amount,
            status=ParkingBookingStatus.ACTIVE,
        )
        space.is_available = False

        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)

        # Load space relation for output
        b_query = (
            select(ParkingBooking)
            .options(selectinload(ParkingBooking.parking_space))
            .where(ParkingBooking.id == booking.id)
        )
        b_res = await self.db.execute(b_query)
        return b_res.scalar_one()

    async def list_user_parking_bookings(self, user_id: uuid.UUID) -> List[ParkingBooking]:
        query = (
            select(ParkingBooking)
            .options(selectinload(ParkingBooking.parking_space))
            .where(ParkingBooking.user_id == user_id)
            .order_by(ParkingBooking.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancel_parking_booking(self, booking_id: uuid.UUID, user: User) -> ParkingBooking:
        query = (
            select(ParkingBooking)
            .options(selectinload(ParkingBooking.parking_space))
            .where(ParkingBooking.id == booking_id)
        )
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()
        if not booking:
            raise ResourceNotFoundError(message="Parking booking not found")

        if booking.user_id != user.id and user.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="Not authorized to cancel this booking")

        booking.status = ParkingBookingStatus.CANCELLED
        if booking.parking_space:
            booking.parking_space.is_available = True

        await self.db.flush()
        await self.db.refresh(booking)
        return booking
