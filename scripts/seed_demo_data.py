"""Seed script to populate database with realistic verified bachelor properties and owners."""

import asyncio
from decimal import Decimal
import uuid
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.property import Property
from app.models.room import Room, RoomSeat, PropertyMedia
from app.core.constants import Gender, PropertyType, RoomType, UserRole
from app.core.security import get_password_hash


async def seed():
    async with AsyncSessionLocal() as session:
        # Check if owner exists
        result = await session.execute(select(User).where(User.email == "owner@bachnest.com"))
        owner = result.scalar_one_or_none()

        if not owner:
            owner = User(
                id=uuid.uuid4(),
                email="owner@bachnest.com",
                phone="+8801711000001",
                hashed_password=get_password_hash("BachNest@123"),
                full_name="Mahmudur Rahman",
                role=UserRole.OWNER,
                gender=Gender.MALE,
                is_active=True,
                is_phone_verified=True,
                is_email_verified=True,
                is_kyc_verified=True,
                trust_score=98.5,
                bio="Verified property owner with 3 premier bachelor residences in Dhaka.",
                institution_or_company="Rahman Estates Ltd",
            )
            session.add(owner)
            await session.flush()
            print(f"Created owner: {owner.email}")

        # Check existing properties
        prop_count_res = await session.execute(select(Property).where(Property.owner_id == owner.id))
        existing_props = prop_count_res.scalars().all()
        if len(existing_props) > 0:
            print(f"Database already has {len(existing_props)} properties. Skipping seeding.")
            return

        # 1. Premium Bachelor Studio in Dhanmondi
        p1 = Property(
            id=uuid.uuid4(),
            owner_id=owner.id,
            title="Luxury Bachelor Studio with Balcony & High-Speed WiFi",
            description="Modern, sunny studio room tailored for IT professionals and university students. Includes full power backup, lift, high-speed optical fiber WiFi, and 24/7 security.",
            property_type=PropertyType.FLAT,
            address_line="Road 27 (Old), Dhanmondi R/A",
            area_neighborhood="Dhanmondi",
            city="Dhaka",
            postal_code="1209",
            latitude=23.7538,
            longitude=90.3768,
            has_lift=True,
            has_generator=True,
            has_cctv=True,
            has_wifi=True,
            gate_closing_time="11:30 PM",
            visitor_policy="Guests allowed until 9:00 PM with NID entry",
            is_published=True,
            is_verified_by_admin=True,
        )
        session.add(p1)
        await session.flush()

        r1 = Room(
            id=uuid.uuid4(),
            property_id=p1.id,
            room_number_or_name="Studio Unit 4B",
            room_type=RoomType.SINGLE,
            monthly_rent=Decimal("12500.00"),
            security_deposit=Decimal("12500.00"),
            has_attached_bathroom=True,
            has_balcony=True,
            has_ac=True,
            is_furnished=True,
            total_capacity=1,
            current_occupancy=0,
            is_available=True,
        )
        session.add(r1)

        m1 = PropertyMedia(
            id=uuid.uuid4(),
            property_id=p1.id,
            media_url="/images/hero-room.jpg",
            media_type="IMAGE",
            caption="Spacious Bachelor Studio Bedroom with Work Desk",
            is_cover=True,
            display_order=1,
        )
        session.add(m1)

        # 2. Modern Single Room in Mirpur DOHS
        p2 = Property(
            id=uuid.uuid4(),
            owner_id=owner.id,
            title="Executive Bachelor Single Room in Secure DOHS",
            description="Peaceful, secure environment in Mirpur DOHS. Close to metro rail station, attached bath, parquet floor, and meal system available on request.",
            property_type=PropertyType.SUBLET,
            address_line="Avenue 4, Road 7, Mirpur DOHS",
            area_neighborhood="Mirpur",
            city="Dhaka",
            postal_code="1216",
            latitude=23.8341,
            longitude=90.3667,
            has_lift=True,
            has_generator=True,
            has_cctv=True,
            has_wifi=True,
            gate_closing_time="11:00 PM",
            visitor_policy="Family and verified friends only",
            is_published=True,
            is_verified_by_admin=True,
        )
        session.add(p2)
        await session.flush()

        r2 = Room(
            id=uuid.uuid4(),
            property_id=p2.id,
            room_number_or_name="Room 302",
            room_type=RoomType.SINGLE,
            monthly_rent=Decimal("8500.00"),
            security_deposit=Decimal("8500.00"),
            has_attached_bathroom=True,
            has_balcony=True,
            has_ac=False,
            is_furnished=True,
            total_capacity=1,
            current_occupancy=0,
            is_available=True,
        )
        session.add(r2)

        m2 = PropertyMedia(
            id=uuid.uuid4(),
            property_id=p2.id,
            media_url="/images/single-room.jpg",
            media_type="IMAGE",
            caption="Bright single bedroom with modern study desk",
            is_cover=True,
            display_order=1,
        )
        session.add(m2)

        # 3. 3-Bed Apartment for Bachelor Group in Bashundhara R/A
        p3 = Property(
            id=uuid.uuid4(),
            owner_id=owner.id,
            title="3-Bed Full Bachelor Flat near NSU & IUB",
            description="Perfect for NSU/IUB university students or startup team. South-facing full apartment with modern kitchen, drawing/dining hall, and lift backup.",
            property_type=PropertyType.FLAT,
            address_line="Block C, Road 5, Bashundhara R/A",
            area_neighborhood="Bashundhara",
            city="Dhaka",
            postal_code="1229",
            latitude=23.8151,
            longitude=90.4255,
            has_lift=True,
            has_generator=True,
            has_cctv=True,
            has_wifi=True,
            gate_closing_time="12:00 AM",
            visitor_policy="Open visitor policy with registration",
            is_published=True,
            is_verified_by_admin=True,
        )
        session.add(p3)
        await session.flush()

        r3 = Room(
            id=uuid.uuid4(),
            property_id=p3.id,
            room_number_or_name="Master Bedroom",
            room_type=RoomType.MASTER,
            monthly_rent=Decimal("15000.00"),
            security_deposit=Decimal("15000.00"),
            has_attached_bathroom=True,
            has_balcony=True,
            has_ac=True,
            is_furnished=True,
            total_capacity=2,
            current_occupancy=0,
            is_available=True,
        )
        session.add(r3)

        m3 = PropertyMedia(
            id=uuid.uuid4(),
            property_id=p3.id,
            media_url="/images/apartment.jpg",
            media_type="IMAGE",
            caption="Spacious living and dining space with scenic view",
            is_cover=True,
            display_order=1,
        )
        session.add(m3)

        await session.commit()
        print("Successfully seeded 3 verified properties with images!")


if __name__ == "__main__":
    asyncio.run(seed())
