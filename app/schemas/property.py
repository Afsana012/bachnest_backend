"""Property, Room, Seat, and Search schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from app.core.constants import PropertyType, RoomType
from app.schemas.common import BaseSchema


class PropertyMediaOut(BaseSchema):
    id: uuid.UUID
    media_url: str
    media_type: str
    caption: Optional[str] = None
    is_cover: bool = False
    display_order: int = 0


class RoomSeatOut(BaseSchema):
    id: uuid.UUID
    room_id: uuid.UUID
    seat_identifier: str
    monthly_rent: Decimal
    is_occupied: bool


class RoomSeatCreate(BaseSchema):
    seat_identifier: str = Field(..., min_length=1, max_length=50)
    monthly_rent: Decimal = Field(..., ge=0)


class RoomCreate(BaseSchema):
    room_number_or_name: str = Field(..., min_length=1, max_length=100)
    room_type: RoomType = RoomType.SINGLE
    monthly_rent: Decimal = Field(..., ge=0)
    security_deposit: Decimal = Field(default=Decimal("0.0"), ge=0)
    has_attached_bathroom: bool = False
    has_balcony: bool = False
    has_ac: bool = False
    is_furnished: bool = False
    total_capacity: int = Field(default=1, ge=1)


class RoomUpdate(BaseSchema):
    room_number_or_name: Optional[str] = None
    room_type: Optional[RoomType] = None
    monthly_rent: Optional[Decimal] = None
    security_deposit: Optional[Decimal] = None
    has_attached_bathroom: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_ac: Optional[bool] = None
    is_furnished: Optional[bool] = None
    is_available: Optional[bool] = None


class RoomOut(BaseSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    room_number_or_name: str
    room_type: RoomType
    monthly_rent: Decimal
    security_deposit: Decimal
    has_attached_bathroom: bool
    has_balcony: bool
    has_ac: bool
    is_furnished: bool
    total_capacity: int
    current_occupancy: int
    is_available: bool
    seats: List[RoomSeatOut] = Field(default_factory=list)


class PropertyCreate(BaseSchema):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    property_type: PropertyType = PropertyType.FLAT
    address_line: str = Field(..., min_length=3, max_length=255)
    area_neighborhood: str = Field(..., min_length=2, max_length=100)
    city: str = Field(default="Dhaka", min_length=2, max_length=100)
    postal_code: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    total_floors: Optional[int] = None
    floor_number: Optional[int] = None
    flat_number: Optional[str] = None
    has_lift: bool = False
    has_generator: bool = False
    has_cctv: bool = False
    has_wifi: bool = False
    gate_closing_time: Optional[str] = None
    visitor_policy: Optional[str] = None


class PropertyMediaCreate(BaseSchema):
    media_url: str = Field(..., min_length=5, max_length=512)
    media_type: str = "IMAGE"
    caption: Optional[str] = None
    is_cover: bool = False
    display_order: int = 0


class PropertyUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[PropertyType] = None
    address_line: Optional[str] = None
    area_neighborhood: Optional[str] = None
    city: Optional[str] = None
    has_lift: Optional[bool] = None
    has_generator: Optional[bool] = None
    has_cctv: Optional[bool] = None
    has_wifi: Optional[bool] = None
    gate_closing_time: Optional[str] = None
    visitor_policy: Optional[str] = None


class PropertyOut(BaseSchema):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str
    property_type: PropertyType
    address_line: str
    area_neighborhood: str
    city: str
    latitude: float
    longitude: float
    has_lift: bool
    has_generator: bool
    has_cctv: bool
    has_wifi: bool
    gate_closing_time: Optional[str] = None
    visitor_policy: Optional[str] = None
    is_published: bool
    is_verified_by_admin: bool
    created_at: datetime
    rooms: List[RoomOut] = Field(default_factory=list)
    media: List[PropertyMediaOut] = Field(default_factory=list)


class SearchPropertyItem(BaseSchema):
    property_id: uuid.UUID
    title: str
    property_type: PropertyType
    area: str
    city: str
    latitude: float
    longitude: float
    starting_rent: Decimal
    available_rooms: int
    tags: List[str] = Field(default_factory=list)
    distance_km: Optional[float] = None
    cover_image_url: Optional[str] = None
