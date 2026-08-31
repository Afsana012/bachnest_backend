"""Search service managing PostGIS geospatial radius and bounding-box queries."""

from decimal import Decimal
from typing import List, Optional, Tuple
import uuid
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakeEnvelope, ST_MakePoint, ST_SetSRID
from sqlalchemy import cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import PropertyType, RoomType
from app.models.property import Property
from app.models.room import Room
from app.schemas.property import SearchPropertyItem


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_properties(
        self,
        city: Optional[str] = None,
        area: Optional[str] = None,
        property_type: Optional[PropertyType] = None,
        budget_min: Optional[Decimal] = None,
        budget_max: Optional[Decimal] = None,
        has_wifi: Optional[bool] = None,
        has_ac: Optional[bool] = None,
        has_lift: Optional[bool] = None,
        has_generator: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[SearchPropertyItem], int]:
        """Search published properties with standard attribute filters."""
        stmt = (
            select(Property)
            .options(selectinload(Property.rooms), selectinload(Property.media))
            .where(Property.is_published == True)
        )

        if city:
            stmt = stmt.where(Property.city.ilike(f"%{city}%"))
        if area:
            stmt = stmt.where(Property.area_neighborhood.ilike(f"%{area}%"))
        if property_type:
            stmt = stmt.where(Property.property_type == property_type)
        if has_wifi is not None:
            stmt = stmt.where(Property.has_wifi == has_wifi)
        if has_lift is not None:
            stmt = stmt.where(Property.has_lift == has_lift)
        if has_generator is not None:
            stmt = stmt.where(Property.has_generator == has_generator)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(stmt)
        properties = result.scalars().all()

        items = []
        for p in properties:
            starting_rent = min([r.monthly_rent for r in p.rooms], default=Decimal("0.0")) if p.rooms else Decimal("0.0")
            
            # Apply budget filters if specified
            if budget_min is not None and starting_rent < budget_min:
                continue
            if budget_max is not None and starting_rent > budget_max:
                continue

            available_rooms = sum(1 for r in p.rooms if r.is_available)
            tags = []
            if p.has_wifi:
                tags.append("WIFI")
            if p.has_lift:
                tags.append("LIFT")
            if p.has_generator:
                tags.append("GENERATOR")

            cover_img = None
            for m in p.media:
                if m.is_cover:
                    cover_img = m.media_url
                    break
            if not cover_img and p.media:
                cover_img = p.media[0].media_url

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
                    tags=tags,
                    cover_image_url=cover_img,
                )
            )

        return items, total

    async def search_map_radius(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0,
        property_type: Optional[PropertyType] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[SearchPropertyItem], int]:
        """Geospatial radius search using PostGIS ST_DWithin and ST_Distance."""
        point_geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        radius_meters = radius_km * 1000.0

        stmt = (
            select(Property)
            .options(selectinload(Property.rooms), selectinload(Property.media))
            .where(
                Property.is_published == True,
                ST_DWithin(
                    Property.location,
                    point_geom,
                    radius_meters
                )
            )
            .order_by(ST_Distance(Property.location, point_geom).asc())
        )

        if property_type:
            stmt = stmt.where(Property.property_type == property_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(stmt)
        properties = result.scalars().all()

        items = []
        for p in properties:
            starting_rent = min([r.monthly_rent for r in p.rooms], default=Decimal("0.0")) if p.rooms else Decimal("0.0")
            available_rooms = sum(1 for r in p.rooms if r.is_available)
            tags = ["WIFI"] if p.has_wifi else []

            # Calculate approximate distance
            import math
            d_lat = math.radians(p.latitude - lat)
            d_lng = math.radians(p.longitude - lng)
            a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(p.latitude)) * math.sin(d_lng / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist_km = round(6371.0 * c, 2)

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
                    tags=tags,
                    distance_km=dist_km,
                )
            )

        return items, total
