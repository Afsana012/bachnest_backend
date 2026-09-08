import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field

from app.core.constants import ParkingBookingStatus, ParkingRentalPlan, VehicleType
from app.schemas.common import BaseSchema


class ParkingSpaceCreate(BaseSchema):
    space_number_or_name: str = Field(..., max_length=100)
    vehicle_type: VehicleType = VehicleType.BIKE
    monthly_rate: Decimal = Field(..., gt=0)
    daily_rate: Optional[Decimal] = Field(default=None, gt=0)
    is_covered: bool = True
    has_cctv: bool = True


class ParkingSpaceUpdate(BaseSchema):
    space_number_or_name: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    monthly_rate: Optional[Decimal] = Field(default=None, gt=0)
    daily_rate: Optional[Decimal] = Field(default=None, gt=0)
    is_covered: Optional[bool] = None
    has_cctv: Optional[bool] = None
    is_available: Optional[bool] = None


class ParkingSpaceOut(BaseSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    space_number_or_name: str
    vehicle_type: VehicleType
    monthly_rate: Decimal
    daily_rate: Optional[Decimal] = None
    is_covered: bool
    has_cctv: bool
    is_available: bool
    created_at: datetime
    updated_at: datetime


class ParkingBookingCreate(BaseSchema):
    rental_plan: ParkingRentalPlan = ParkingRentalPlan.MONTHLY
    vehicle_registration_number: str = Field(..., min_length=3, max_length=50)
    start_date: date
    end_date: Optional[date] = None


class ParkingBookingOut(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    parking_space_id: uuid.UUID
    rental_plan: ParkingRentalPlan
    vehicle_registration_number: str
    start_date: date
    end_date: Optional[date] = None
    total_amount: Decimal
    status: ParkingBookingStatus
    created_at: datetime
    updated_at: datetime
    parking_space: Optional[ParkingSpaceOut] = None


class ParkingSearchItem(BaseSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    property_title: str
    property_address: str
    area_neighborhood: str
    city: str
    space_number_or_name: str
    vehicle_type: VehicleType
    monthly_rate: Decimal
    daily_rate: Optional[Decimal] = None
    is_covered: bool
    has_cctv: bool
    is_available: bool
    owner_name: str
    owner_phone: str
