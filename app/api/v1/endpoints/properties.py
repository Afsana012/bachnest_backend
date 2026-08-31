"""Property, Room, Seat, and Geospatial Search API endpoints."""

from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import PropertyType, RoomType, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.schemas.kyc import CompatibilityResult, RoommatePreferenceCreate, RoommatePreferenceOut
from app.schemas.property import (
    PropertyCreate,
    PropertyMediaCreate,
    PropertyOut,
    PropertyUpdate,
    RoomCreate,
    RoomOut,
    RoomSeatCreate,
    RoomSeatOut,
    RoomUpdate,
    SearchPropertyItem,
)
from app.services.property_service import PropertyService
from app.services.room_service import RoomService
from app.services.roommate_service import RoommateService
from app.services.search_service import SearchService

properties_router = APIRouter(prefix="/properties", tags=["Properties"])
owner_properties_router = APIRouter(prefix="/owner/properties", tags=["Owner Properties"])
rooms_router = APIRouter(tags=["Rooms & Seats"])
search_router = APIRouter(prefix="/search", tags=["Search"])


# --- PROPERTY ENDPOINTS ---
@properties_router.get("", response_model=StandardResponse[List[PropertyOut]])
async def list_properties(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List published properties for public browsing."""
    property_service = PropertyService(db)
    properties = await property_service.list_public_properties(page=page, size=size)
    return StandardResponse(
        success=True,
        message="Properties retrieved successfully",
        data=[PropertyOut.model_validate(p) for p in properties],
    )


@properties_router.post("", response_model=StandardResponse[PropertyOut], status_code=status.HTTP_201_CREATED)
async def create_property(
    req: PropertyCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new property listing (Owner only)."""
    property_service = PropertyService(db)
    prop = await property_service.create_property(current_user, req)
    return StandardResponse(
        success=True,
        message="Property listing created successfully",
        data=PropertyOut.model_validate(prop),
    )


@properties_router.get("/{property_id}", response_model=StandardResponse[PropertyOut])
async def get_property_by_id(property_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed information about a property."""
    property_service = PropertyService(db)
    prop = await property_service.get_property_by_id(property_id)
    return StandardResponse(
        success=True,
        message="Property details retrieved",
        data=PropertyOut.model_validate(prop),
    )


@properties_router.patch("/{property_id}", response_model=StandardResponse[PropertyOut])
async def update_property(
    property_id: uuid.UUID,
    req: PropertyUpdate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update property details (Owner only)."""
    property_service = PropertyService(db)
    prop = await property_service.update_property(property_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Property updated successfully",
        data=PropertyOut.model_validate(prop),
    )


@properties_router.delete("/{property_id}", response_model=StandardResponse[dict])
async def delete_property(
    property_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a property listing (Owner only)."""
    property_service = PropertyService(db)
    await property_service.delete_property(property_id, current_user)
    return StandardResponse(
        success=True,
        message="Property deleted successfully",
        data={"property_id": str(property_id)},
    )


@properties_router.patch("/{property_id}/publish", response_model=StandardResponse[PropertyOut])
async def publish_property(
    property_id: uuid.UUID,
    is_published: bool = Query(True),
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Publish or unpublish a property listing."""
    property_service = PropertyService(db)
    prop = await property_service.set_publish_status(property_id, current_user, is_published)
    return StandardResponse(
        success=True,
        message="Property publication status updated",
        data=PropertyOut.model_validate(prop),
    )


@owner_properties_router.get("", response_model=StandardResponse[List[PropertyOut]])
async def list_my_properties(
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """List all properties owned by the current logged in owner."""
    property_service = PropertyService(db)
    properties = await property_service.list_owner_properties(current_user.id)
    return StandardResponse(
        success=True,
        message="Owner properties retrieved",
        data=[PropertyOut.model_validate(p) for p in properties],
    )


@properties_router.post("/{property_id}/media", response_model=StandardResponse[PropertyOut], status_code=status.HTTP_201_CREATED)
async def attach_property_media(
    property_id: uuid.UUID,
    items: List[PropertyMediaCreate],
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Attach uploaded media URLs to a property."""
    property_service = PropertyService(db)
    prop = await property_service.add_media(property_id, current_user, items)
    return StandardResponse(
        success=True,
        message="Media attached successfully",
        data=PropertyOut.model_validate(prop),
    )


@properties_router.post("/upload-media", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
async def upload_property_media(
    file: UploadFile = File(...),
    folder: str = Query("properties", description="Upload folder e.g. properties, kyc, avatar"),
    current_user: User = Depends(get_current_user),
):
    """Upload media image to Cloudflare R2 object storage."""
    from app.integrations.storage.base import get_storage_provider

    content = await file.read()
    storage = get_storage_provider()
    file_url = await storage.upload(
        file_content=content,
        filename=file.filename or "upload.jpg",
        content_type=file.content_type or "image/jpeg",
        folder=folder,
    )
    return StandardResponse(
        success=True,
        message="Media uploaded successfully to Cloudflare R2",
        data={"file_url": file_url, "filename": file.filename},
    )



# --- ROOM ENDPOINTS ---
@rooms_router.post("/properties/{property_id}/rooms", response_model=StandardResponse[RoomOut], status_code=status.HTTP_201_CREATED)
async def create_room(
    property_id: uuid.UUID,
    req: RoomCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Add a room to a property."""
    room_service = RoomService(db)
    room = await room_service.create_room(property_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Room added successfully",
        data=RoomOut.model_validate(room),
    )


@rooms_router.get("/properties/{property_id}/rooms", response_model=StandardResponse[List[RoomOut]])
async def list_rooms(property_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all rooms belonging to a property."""
    room_service = RoomService(db)
    rooms = await room_service.list_rooms(property_id)
    return StandardResponse(
        success=True,
        message="Rooms retrieved",
        data=[RoomOut.model_validate(r) for r in rooms],
    )


@rooms_router.get("/rooms/{room_id}", response_model=StandardResponse[RoomOut])
async def get_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get single room details."""
    room_service = RoomService(db)
    room = await room_service.get_room_by_id(room_id)
    return StandardResponse(
        success=True,
        message="Room details retrieved",
        data=RoomOut.model_validate(room),
    )


@rooms_router.patch("/rooms/{room_id}", response_model=StandardResponse[RoomOut])
async def update_room(
    room_id: uuid.UUID,
    req: RoomUpdate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update room details."""
    room_service = RoomService(db)
    room = await room_service.update_room(room_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Room updated successfully",
        data=RoomOut.model_validate(room),
    )


@rooms_router.delete("/rooms/{room_id}", response_model=StandardResponse[dict])
async def delete_room(
    room_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a room."""
    room_service = RoomService(db)
    await room_service.delete_room(room_id, current_user)
    return StandardResponse(
        success=True,
        message="Room deleted successfully",
        data={"room_id": str(room_id)},
    )


# --- SEAT ENDPOINTS ---
@rooms_router.post("/rooms/{room_id}/seats", response_model=StandardResponse[RoomSeatOut], status_code=status.HTTP_201_CREATED)
async def create_seat(
    room_id: uuid.UUID,
    req: RoomSeatCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Add a seat to a shared room."""
    room_service = RoomService(db)
    seat = await room_service.create_seat(room_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Seat added successfully",
        data=RoomSeatOut.model_validate(seat),
    )


@rooms_router.get("/rooms/{room_id}/seats", response_model=StandardResponse[List[RoomSeatOut]])
async def list_seats(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all seats in a room."""
    room_service = RoomService(db)
    seats = await room_service.list_seats(room_id)
    return StandardResponse(
        success=True,
        message="Seats retrieved",
        data=[RoomSeatOut.model_validate(s) for s in seats],
    )


@rooms_router.patch("/seats/{seat_id}", response_model=StandardResponse[RoomSeatOut])
async def update_seat(
    seat_id: uuid.UUID,
    req: RoomSeatCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Update seat details."""
    room_service = RoomService(db)
    seat = await room_service.update_seat(seat_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Seat updated successfully",
        data=RoomSeatOut.model_validate(seat),
    )


@rooms_router.delete("/seats/{seat_id}", response_model=StandardResponse[dict])
async def delete_seat(
    seat_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a seat."""
    room_service = RoomService(db)
    await room_service.delete_seat(seat_id, current_user)
    return StandardResponse(
        success=True,
        message="Seat deleted successfully",
        data={"seat_id": str(seat_id)},
    )


# --- SEARCH ENDPOINTS ---
@search_router.get("/properties", response_model=PaginatedResponse[SearchPropertyItem])
async def search_properties(
    city: Optional[str] = Query(None),
    area: Optional[str] = None,
    property_type: Optional[PropertyType] = None,
    budget_min: Optional[Decimal] = None,
    budget_max: Optional[Decimal] = None,
    has_wifi: Optional[bool] = None,
    has_ac: Optional[bool] = None,
    has_lift: Optional[bool] = None,
    has_generator: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search available properties with attribute filters."""
    search_service = SearchService(db)
    items, total = await search_service.search_properties(
        city=city,
        area=area,
        property_type=property_type,
        budget_min=budget_min,
        budget_max=budget_max,
        has_wifi=has_wifi,
        has_ac=has_ac,
        has_lift=has_lift,
        has_generator=has_generator,
        page=page,
        limit=limit,
    )
    total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
    return PaginatedResponse(
        success=True,
        message="Properties retrieved",
        items=items,
        meta=PaginationMeta(page=page, limit=limit, total=total, total_pages=total_pages),
    )


@search_router.get("/map", response_model=PaginatedResponse[SearchPropertyItem])
async def search_map_radius(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(5.0, ge=0.5, le=50.0, description="Radius in kilometers"),
    property_type: Optional[PropertyType] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Geospatial radius search centered at GPS coordinates using PostGIS."""
    search_service = SearchService(db)
    items, total = await search_service.search_map_radius(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        property_type=property_type,
        page=page,
        limit=limit,
    )
    total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
    return PaginatedResponse(
        success=True,
        message="Map search results retrieved",
        items=items,
        meta=PaginationMeta(page=page, limit=limit, total=total, total_pages=total_pages),
    )


@search_router.get("/roommates", response_model=StandardResponse[List[CompatibilityResult]])
async def search_compatible_roommates(
    current_user: User = Depends(require_roles(UserRole.BACHELOR)),
    db: AsyncSession = Depends(get_db),
):
    """Find compatible potential roommates based on lifestyle habits and preferences."""
    from sqlalchemy import select
    roommate_service = RoommateService(db)
    users_query = select(User).where(
        User.role == UserRole.BACHELOR,
        User.id != current_user.id,
        User.is_active == True,
    ).limit(20)
    candidates = (await db.execute(users_query)).scalars().all()

    results = []
    for cand in candidates:
        comp = await roommate_service.calculate_compatibility(current_user, cand)
        results.append(comp)

    results.sort(key=lambda x: x.compatibility_score, reverse=True)
    return StandardResponse(
        success=True,
        message="Roommate compatibility rankings calculated",
        data=results,
    )
