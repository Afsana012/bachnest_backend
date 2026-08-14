"""Property, Room, and Search API endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import PropertyType, RoomType, UserRole
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.property import Property
from app.models.room import Room, RoomSeat
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.schemas.property import (
    PropertyCreate,
    PropertyOut,
    PropertyUpdate,
    RoomCreate,
    RoomOut,
    RoomSeatCreate,
    RoomSeatOut,
    RoomUpdate,
    SearchPropertyItem,
)

properties_router = APIRouter(prefix="/properties", tags=["Properties"])
rooms_router = APIRouter(tags=["Rooms & Seats"])
search_router = APIRouter(prefix="/search", tags=["Search"])


# --- PROPERTY ENDPOINTS ---
@properties_router.post("", response_model=StandardResponse[PropertyOut], status_code=status.HTTP_201_CREATED)
async def create_property(
    req: PropertyCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new property listing (Owner only)."""
    property_obj = Property(
        owner_id=current_user.id,
        **req.model_dump()
    )
    db.add(property_obj)
    await db.flush()
    await db.refresh(property_obj)
    return StandardResponse(
        success=True,
        message="Property listing created successfully",
        data=PropertyOut.model_validate(property_obj)
    )


@properties_router.get("/{property_id}", response_model=StandardResponse[PropertyOut])
async def get_property_by_id(property_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed information about a property."""
    query = (
        select(Property)
        .options(selectinload(Property.rooms).selectinload(Room.seats), selectinload(Property.media))
        .where(Property.id == property_id)
    )
    result = await db.execute(query)
    prop = result.scalar_one_or_none()
    if not prop:
        raise ResourceNotFoundError(message="Property not found")
    return StandardResponse(
        success=True,
        message="Property details retrieved",
        data=PropertyOut.model_validate(prop)
    )


@properties_router.patch("/{property_id}", response_model=StandardResponse[PropertyOut])
async def update_property(
    property_id: uuid.UUID,
    req: PropertyUpdate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db)
):
    """Update property details (Owner only)."""
    query = select(Property).where(Property.id == property_id)
    result = await db.execute(query)
    prop = result.scalar_one_or_none()
    if not prop:
        raise ResourceNotFoundError(message="Property not found")
    if prop.owner_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise PermissionDeniedError(message="You do not own this property")

    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(prop, field, val)

    await db.flush()
    await db.refresh(prop)
    return StandardResponse(
        success=True,
        message="Property updated successfully",
        data=PropertyOut.model_validate(prop)
    )


# --- ROOM ENDPOINTS ---
@rooms_router.post("/properties/{property_id}/rooms", response_model=StandardResponse[RoomOut], status_code=status.HTTP_201_CREATED)
async def create_room(
    property_id: uuid.UUID,
    req: RoomCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db)
):
    """Add a room to a property."""
    prop_query = select(Property).where(Property.id == property_id)
    prop = (await db.execute(prop_query)).scalar_one_or_none()
    if not prop:
        raise ResourceNotFoundError(message="Property not found")
    if prop.owner_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise PermissionDeniedError(message="You do not own this property")

    room = Room(property_id=property_id, **req.model_dump())
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return StandardResponse(
        success=True,
        message="Room added successfully",
        data=RoomOut.model_validate(room)
    )


# --- SEARCH ENDPOINTS ---
@search_router.get("/properties", response_model=PaginatedResponse[SearchPropertyItem])
async def search_properties(
    city: Optional[str] = Query("Dhaka"),
    area: Optional[str] = None,
    property_type: Optional[PropertyType] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search available properties with filters."""
    stmt = (
        select(Property)
        .options(selectinload(Property.rooms))
        .where(Property.is_published == True)
    )
    if city:
        stmt = stmt.where(Property.city.ilike(f"%{city}%"))
    if area:
        stmt = stmt.where(Property.area_neighborhood.ilike(f"%{area}%"))
    if property_type:
        stmt = stmt.where(Property.property_type == property_type)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    properties = result.scalars().all()

    items = []
    for p in properties:
        starting_rent = min([r.monthly_rent for r in p.rooms], default=0) if p.rooms else 0
        available_rooms = sum(1 for r in p.rooms if r.is_available)
        items.append(
            SearchPropertyItem(
                property_id=p.id,
                title=p.title,
                property_type=p.property_type,
                area=p.area_neighborhood,
                city=p.city,
                latitude=p.latitude,
                longitude=p.longitude,
                starting_rent=starting_rent,
                available_rooms=available_rooms,
                tags=["WIFI"] if p.has_wifi else [],
            )
        )

    return PaginatedResponse(
        success=True,
        message="Properties retrieved",
        items=items,
        meta=PaginationMeta(page=page, limit=limit, total=len(items), total_pages=1)
    )
