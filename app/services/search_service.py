"""Search service managing radius and attribute queries."""

import math
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import PropertyType
from app.models.property import Property
from app.models.room import Room
from app.schemas.property import SearchPropertyItem

EARTH_RADIUS_KM = 6371.0
KM_PER_DEGREE_LAT = 111.045


def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


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
        if has_ac is not None:
            stmt = stmt.where(
                exists(select(Room.id).where(Room.property_id == Property.id, Room.has_ac == has_ac))
            )

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
        """Radius search using a bounding-box prefilter plus haversine distance."""
        lat_delta = radius_km / KM_PER_DEGREE_LAT
        lng_delta = radius_km / (KM_PER_DEGREE_LAT * math.cos(math.radians(lat)))
        if lng_delta <= 0 or math.isnan(lng_delta) or math.isinf(lng_delta):
            lng_delta = 180.0

        conditions = [
            Property.is_published == True,
            Property.latitude.between(lat - lat_delta, lat + lat_delta),
            Property.longitude.between(lng - lng_delta, lng + lng_delta),
        ]
        if property_type:
            conditions.append(Property.property_type == property_type)

        distance_expr = EARTH_RADIUS_KM * func.acos(
            func.least(
                1.0,
                func.cos(math.radians(lat))
                * func.cos(func.radians(Property.latitude))
                * func.cos(func.radians(Property.longitude) - math.radians(lng))
                + func.sin(math.radians(lat)) * func.sin(func.radians(Property.latitude)),
            )
        )

        count_stmt = select(func.count()).select_from(Property).where(*conditions)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(Property)
            .options(selectinload(Property.rooms), selectinload(Property.media))
            .where(*conditions)
            .order_by(distance_expr.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        properties = result.scalars().all()

        items = []
        for p in properties:
            starting_rent = min([r.monthly_rent for r in p.rooms], default=Decimal("0.0")) if p.rooms else Decimal("0.0")
            available_rooms = sum(1 for r in p.rooms if r.is_available)
            tags = ["WIFI"] if p.has_wifi else []

            dist_km = round(haversine_distance_km(lat, lng, p.latitude, p.longitude), 2)

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
                    cover_image_url=next(
                        (m.media_url for m in p.media if m.is_cover),
                        p.media[0].media_url if p.media else None,
                    ),
                    distance_km=dist_km,
                )
            )

        return items, total
