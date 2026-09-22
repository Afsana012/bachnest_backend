"""Seed parking spaces for major properties across Dhaka."""

import asyncio
from decimal import Decimal
import uuid
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.parking import ParkingSpace
from app.models.property import Property
from app.core.constants import VehicleType

SPOTS_DATA = [
    {
        "area_match": "Dhanmondi",
        "prop_title_match": "Sunlit 3-Bed Flat",
        "spaces": [
            {
                "space_number_or_name": "Bay G-01 (Covered Bike)",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1500.00"),
                "daily_rate": Decimal("80.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
            {
                "space_number_or_name": "Slot P-1 (Basement Car)",
                "vehicle_type": VehicleType.CAR,
                "monthly_rate": Decimal("4500.00"),
                "daily_rate": Decimal("250.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "Uttara",
        "prop_title_match": "Modern Family Flat in Uttara",
        "spaces": [
            {
                "space_number_or_name": "Lot B-2 (Motorcycle Bay)",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1200.00"),
                "daily_rate": Decimal("60.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
            {
                "space_number_or_name": "Car Bay #3 (Ground Garage)",
                "vehicle_type": VehicleType.CAR,
                "monthly_rate": Decimal("4000.00"),
                "daily_rate": Decimal("220.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "Banani",
        "prop_title_match": "Banani",
        "spaces": [
            {
                "space_number_or_name": "Banani Scooty & Bike Bay 1",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1800.00"),
                "daily_rate": Decimal("100.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
            {
                "space_number_or_name": "Banani Covered Car Slot 1A",
                "vehicle_type": VehicleType.CAR,
                "monthly_rate": Decimal("5500.00"),
                "daily_rate": Decimal("300.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "Mohakhali",
        "prop_title_match": "Mohakhali",
        "spaces": [
            {
                "space_number_or_name": "Mohakhali Bike Garage Slot 4",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1400.00"),
                "daily_rate": Decimal("75.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
            {
                "space_number_or_name": "Mohakhali Car Bay #2",
                "vehicle_type": VehicleType.CAR,
                "monthly_rate": Decimal("4800.00"),
                "daily_rate": Decimal("250.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "Bashundhora",
        "prop_title_match": "bachelor point",
        "spaces": [
            {
                "space_number_or_name": "Bashundhara R/A Bike Slot 3",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1200.00"),
                "daily_rate": Decimal("60.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
            {
                "space_number_or_name": "Bashundhara Car Garage Lot 1",
                "vehicle_type": VehicleType.CAR,
                "monthly_rate": Decimal("3800.00"),
                "daily_rate": Decimal("200.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "Badda",
        "prop_title_match": "Student Hostel",
        "spaces": [
            {
                "space_number_or_name": "Badda IUB Student Bike Bay",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1000.00"),
                "daily_rate": Decimal("50.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "Mirpur DOHS",
        "prop_title_match": "Mirpur DOHS",
        "spaces": [
            {
                "space_number_or_name": "DOHS Secured Bike Bay 7",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1500.00"),
                "daily_rate": Decimal("80.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
            {
                "space_number_or_name": "DOHS Covered Car Spot C-4",
                "vehicle_type": VehicleType.CAR,
                "monthly_rate": Decimal("4500.00"),
                "daily_rate": Decimal("240.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
    {
        "area_match": "mirpur",
        "prop_title_match": "Gents Mess",
        "spaces": [
            {
                "space_number_or_name": "Mirpur-12 Bike Stand Slot 5",
                "vehicle_type": VehicleType.BIKE,
                "monthly_rate": Decimal("1100.00"),
                "daily_rate": Decimal("55.00"),
                "is_covered": True,
                "has_cctv": True,
                "is_available": True,
            },
        ],
    },
]


async def run():
    async with AsyncSessionLocal() as db:
        # Update existing slot 3 and slot 6 daily rates if missing
        res = await db.execute(select(ParkingSpace))
        existing_spaces = res.scalars().all()
        for s in existing_spaces:
            if s.space_number_or_name == "slot 3" and not s.daily_rate:
                s.daily_rate = Decimal("150.00")
            elif s.space_number_or_name == "slot 6" and not s.daily_rate:
                s.daily_rate = Decimal("80.00")

        # Also publish afsana's house
        prop_res = await db.execute(
            select(Property).where(Property.id == uuid.UUID("638668a6-01a7-4ae1-b09b-bac1118aaeef"))
        )
        afsana_prop = prop_res.scalar_one_or_none()
        if afsana_prop and not afsana_prop.is_published:
            afsana_prop.is_published = True
            print("Published afsana's house")

        # Now check properties for each item and add parking space if not already added
        props_res = await db.execute(select(Property))
        all_props = props_res.scalars().all()

        added_count = 0
        for entry in SPOTS_DATA:
            matched_prop = None
            for p in all_props:
                if (
                    entry["area_match"].lower() in (p.area_neighborhood or "").lower()
                    and entry["prop_title_match"].lower() in (p.title or "").lower()
                ):
                    matched_prop = p
                    break

            if not matched_prop:
                for p in all_props:
                    if entry["area_match"].lower() in (p.area_neighborhood or "").lower():
                        matched_prop = p
                        break

            if not matched_prop:
                print(f"No property found for area: {entry['area_match']}")
                continue

            for s_info in entry["spaces"]:
                # Check if space already exists on this property
                check_q = select(ParkingSpace).where(
                    ParkingSpace.property_id == matched_prop.id,
                    ParkingSpace.space_number_or_name == s_info["space_number_or_name"],
                )
                existing = (await db.execute(check_q)).scalar_one_or_none()
                if not existing:
                    new_space = ParkingSpace(
                        id=uuid.uuid4(),
                        property_id=matched_prop.id,
                        space_number_or_name=s_info["space_number_or_name"],
                        vehicle_type=s_info["vehicle_type"],
                        monthly_rate=s_info["monthly_rate"],
                        daily_rate=s_info["daily_rate"],
                        is_covered=s_info["is_covered"],
                        has_cctv=s_info["has_cctv"],
                        is_available=s_info["is_available"],
                    )
                    db.add(new_space)
                    added_count += 1
                    print(f"Added space '{s_info['space_number_or_name']}' for property '{matched_prop.title}' ({matched_prop.area_neighborhood})")

        await db.commit()
        print(f"Total new spaces added: {added_count}")


if __name__ == "__main__":
    asyncio.run(run())
