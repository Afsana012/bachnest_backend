"""Seed realistic demo properties with Unsplash media for the owner account."""

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.property import Property
from app.models.room import PropertyMedia, Room, RoomSeat
from app.models.user import User

OWNER_EMAIL = "ahad@gmail.com"
BASE_URL = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=1200&q=80"

PHOTOS = {
    "living1": "1522708323590-d24dbb6b0267",
    "living2": "1493809842364-78817add7ffb",
    "living3": "1586023492125-27b2c045efd7",
    "living4": "1598928506311-c55ded91a20c",
    "interior1": "1560448204-e02f11c3d0e2",
    "interior2": "1560185127-6ed189bf02f4",
    "interior3": "1560184897-ae75f418493e",
    "apartment": "1502672260266-1c1ef2d93688",
    "building1": "1560185007-cde436f6a4d0",
    "building2": "1515263487990-61b07816b324",
    "bedroom1": "1505691938895-1758d7feb511",
    "bedroom2": "1571508601891-ca5e7a713859",
    "bedroom3": "1595526114035-0d45ed16cfbf",
    "bedroom4": "1615874959474-d609969a20ed",
    "kitchen": "1484154218962-a197022b5858",
    "bathroom": "1552321554-5fefe8c9ef14",
    "hotel1": "1611892440504-42a792e24d32",
    "hotel2": "1567767292278-a4f21aa2d36e",
    "hotel3": "1512918728675-ed5a9ecdebfd",
    "bunk": "1540518614846-7eded433c457",
}


def img(key: str) -> str:
    return BASE_URL.format(PHOTOS[key])


PROPERTIES = [
    {
        "title": "Sunlit 3-Bed Flat Beside Dhanmondi Lake",
        "description": "South-facing flat on the 5th floor with lake view, full tiles flooring and gas line. Two minutes walk from Dhanmondi 27 bus stop, close to Samrat and Star Kabab. Ideal for a small family or three bachelors sharing.",
        "property_type": "FLAT",
        "address_line": "House 32, Road 27, Old Dhanmondi",
        "area_neighborhood": "Dhanmondi",
        "latitude": 23.7461,
        "longitude": 90.3762,
        "total_floors": 7,
        "floor_number": 5,
        "flat_number": "5-B",
        "has_lift": True,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "is_verified_by_admin": True,
        "media": [("living1", "Living space"), ("kitchen", "Kitchen"), ("bedroom1", "Master bedroom"), ("bathroom", "Attached bathroom")],
        "rooms": [
            {"name": "Master Bedroom", "type": "MASTER", "rent": 16000, "deposit": 16000, "bath": True, "balcony": True, "ac": True, "furnished": True, "capacity": 2},
            {"name": "Bedroom 2", "type": "SINGLE", "rent": 12000, "deposit": 12000, "bath": False, "balcony": True, "ac": False, "furnished": True, "capacity": 1},
            {"name": "Bedroom 3", "type": "SINGLE", "rent": 11000, "deposit": 11000, "bath": False, "balcony": False, "ac": False, "furnished": False, "capacity": 1},
        ],
    },
    {
        "title": "Modern Family Flat in Uttara Sector 7",
        "description": "Newly built 1650 sft flat with three bedrooms, three bathrooms, servant quarter and two balconies. Generator and lift with 24/7 water supply. Walking distance from Rajlakshmi complex and sector 7 market.",
        "property_type": "FLAT",
        "address_line": "Plot 14, Road 3, Sector 7",
        "area_neighborhood": "Uttara",
        "latitude": 23.8667,
        "longitude": 90.4010,
        "total_floors": 9,
        "floor_number": 6,
        "flat_number": "6-A",
        "has_lift": True,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "is_verified_by_admin": True,
        "media": [("apartment", "Flat exterior"), ("living2", "Drawing room"), ("bedroom2", "Bedroom"), ("kitchen", "Kitchen")],
        "rooms": [
            {"name": "Master Bedroom", "type": "MASTER", "rent": 15000, "deposit": 30000, "bath": True, "balcony": True, "ac": True, "furnished": True, "capacity": 2},
            {"name": "Bedroom 2", "type": "SINGLE", "rent": 12000, "deposit": 24000, "bath": True, "balcony": False, "ac": False, "furnished": False, "capacity": 2},
        ],
    },
    {
        "title": "Corner Flat with Park View in Bashundhara R/A",
        "description": "Corner unit facing the block park with cross ventilation and natural light all day. Modular kitchen, imported tiles and concealed wiring. Very close to Jaago school and Konabari bridge route.",
        "property_type": "FLAT",
        "address_line": "House 44, Block C, Bashundhara R/A",
        "area_neighborhood": "Bashundhara",
        "latitude": 23.8103,
        "longitude": 90.4296,
        "total_floors": 6,
        "floor_number": 4,
        "flat_number": "4-C",
        "has_lift": True,
        "has_generator": True,
        "has_cctv": False,
        "has_wifi": True,
        "is_verified_by_admin": False,
        "media": [("living3", "Living room"), ("interior1", "Dining space"), ("bedroom3", "Bedroom"), ("bathroom", "Bathroom")],
        "rooms": [
            {"name": "Master Bedroom", "type": "MASTER", "rent": 14000, "deposit": 14000, "bath": True, "balcony": True, "ac": True, "furnished": False, "capacity": 2},
            {"name": "Bedroom 2", "type": "SINGLE", "rent": 10000, "deposit": 10000, "bath": False, "balcony": True, "ac": False, "furnished": False, "capacity": 1},
            {"name": "Bedroom 3", "type": "SINGLE", "rent": 9500, "deposit": 9500, "bath": False, "balcony": False, "ac": False, "furnished": False, "capacity": 1},
        ],
    },
    {
        "title": "Budget Bachelor Flat in Mohammadpur",
        "description": "Simple and clean 2-bedroom flat on ground floor, suitable for four working bachelors. Rickshaw stand at the door, five minutes from Town Hall market. Water and gas supply stable.",
        "property_type": "FLAT",
        "address_line": "45/A Shyamoli Ring Road, Mohammadpur",
        "area_neighborhood": "Mohammadpur",
        "latitude": 23.7657,
        "longitude": 90.3620,
        "total_floors": 4,
        "floor_number": 1,
        "flat_number": "1-A",
        "has_lift": False,
        "has_generator": False,
        "has_cctv": False,
        "has_wifi": True,
        "is_verified_by_admin": False,
        "media": [("interior2", "Living space"), ("bedroom4", "Bedroom"), ("kitchen", "Kitchen")],
        "rooms": [
            {"name": "Bedroom 1", "type": "SHARED", "rent": 8000, "deposit": 8000, "bath": False, "balcony": False, "ac": False, "furnished": True, "capacity": 2},
            {"name": "Bedroom 2", "type": "SHARED", "rent": 7500, "deposit": 7500, "bath": False, "balcony": False, "ac": False, "furnished": True, "capacity": 2},
        ],
    },
    {
        "title": "Private Room Sublet for Working Bachelor in Mirpur DOHS",
        "description": "One furnished room with attached bathroom available in a shared flat from next month. WiFi, cleaned twice a week and utility bills split equally among three flatmates. Ladies market and DOHS park nearby.",
        "property_type": "SUBLET",
        "address_line": "Flat 3-B, Avenue 4, Mirpur DOHS",
        "area_neighborhood": "Mirpur DOHS",
        "latitude": 23.8352,
        "longitude": 90.3674,
        "total_floors": 6,
        "floor_number": 3,
        "flat_number": "3-B",
        "has_lift": True,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "is_verified_by_admin": True,
        "media": [("bedroom1", "Room for rent"), ("living4", "Shared living"), ("kitchen", "Shared kitchen")],
        "rooms": [
            {"name": "Furnished Room", "type": "SINGLE", "rent": 13000, "deposit": 13000, "bath": True, "balcony": False, "ac": True, "furnished": True, "capacity": 1},
        ],
    },
    {
        "title": "Female-Only Sublet Near Mohakhali Gulshan Link Road",
        "description": "Separate furnished room in a girls-only flat with home-cooked dinner option. Building has lift, generator and CCTV. Walking distance to BRAC University shuttle point and Gulshan link road offices.",
        "property_type": "SUBLET",
        "address_line": "House 71, Road 13, Mohakhali DOHS",
        "area_neighborhood": "Mohakhali",
        "latitude": 23.7806,
        "longitude": 90.4029,
        "total_floors": 8,
        "floor_number": 5,
        "flat_number": "5-D",
        "has_lift": True,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "is_verified_by_admin": True,
        "media": [("bedroom2", "Furnished room"), ("hotel1", "Shared lounge"), ("bathroom", "Attached bathroom")],
        "rooms": [
            {"name": "Furnished Room", "type": "SINGLE", "rent": 12500, "deposit": 12500, "bath": True, "balcony": True, "ac": False, "furnished": True, "capacity": 1},
        ],
    },
    {
        "title": "Gents Mess with 12 Seats in Mirpur-12",
        "description": "Established gents mess running for six years. Three meals a day included, RO drinking water and free WiFi. Two seats currently vacant. Five minutes from Mirpur-12 roundabout andTechnical More.",
        "property_type": "MESS",
        "address_line": "88 Pallabi Main Road, Mirpur-12",
        "area_neighborhood": "Mirpur",
        "latitude": 23.8295,
        "longitude": 90.3564,
        "total_floors": 5,
        "floor_number": 2,
        "has_lift": False,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "gate_closing_time": "11:30 PM",
        "visitor_policy": "Day visitors allowed in common area only",
        "is_verified_by_admin": True,
        "media": [("bunk", "Shared room"), ("living3", "Dining space"), ("kitchen", "Mess kitchen")],
        "rooms": [
            {"name": "Room A", "type": "SHARED", "rent": 5500, "deposit": 5500, "bath": True, "balcony": False, "ac": False, "furnished": True, "capacity": 4,
             "seats": [("Bed A-1", 5500, False), ("Bed A-2", 5500, True), ("Bed A-3", 5800, False), ("Bed A-4", 5500, True)]},
            {"name": "Room B", "type": "SHARED", "rent": 5200, "deposit": 5200, "bath": False, "balcony": False, "ac": False, "furnished": True, "capacity": 4,
             "seats": [("Bed B-1", 5200, False), ("Bed B-2", 5200, False), ("Bed B-3", 5200, True), ("Bed B-4", 5400, False)]},
        ],
    },
    {
        "title": "Azimpur Ladies Mess Near New Market",
        "description": "Safe and quiet ladies mess for students and job holders, two minutes from Azimpur bus stop and ten minutes walk to New Market. Home-style cooking, purified water and a female housekeeper stays on site.",
        "property_type": "MESS",
        "address_line": "23/2 Azimpur Staff Quarter Road",
        "area_neighborhood": "Azimpur",
        "latitude": 23.7333,
        "longitude": 90.3917,
        "total_floors": 4,
        "floor_number": 3,
        "has_lift": False,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "gate_closing_time": "10:30 PM",
        "visitor_policy": "No male visitors beyond reception",
        "is_verified_by_admin": False,
        "media": [("bedroom3", "Shared bedroom"), ("interior3", "Study corner"), ("living2", "Common area")],
        "rooms": [
            {"name": "Room 1", "type": "SHARED", "rent": 5000, "deposit": 5000, "bath": True, "balcony": False, "ac": False, "furnished": True, "capacity": 3,
             "seats": [("Bed 1", 5000, False), ("Bed 2", 5000, True), ("Bed 3", 5000, False)]},
            {"name": "Room 2", "type": "SHARED", "rent": 5300, "deposit": 5300, "bath": False, "balcony": True, "ac": False, "furnished": True, "capacity": 2,
             "seats": [("Bed 1", 5300, False), ("Bed 2", 5600, False)]},
        ],
    },
    {
        "title": "Nest Female Hostel in Banani with AC Rooms",
        "description": "Premium female hostel with twin-sharing AC rooms, attached bathrooms and complimentary breakfast. Gym corner, rooftop lounge and laundry service included. CAMS, refreshments and 24/7 security guard.",
        "property_type": "HOSTEL",
        "address_line": "Kemal Ataturk Avenue 21, Banani",
        "area_neighborhood": "Banani",
        "latitude": 23.7925,
        "longitude": 90.4034,
        "total_floors": 10,
        "floor_number": 7,
        "has_lift": True,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "gate_closing_time": "11:00 PM",
        "visitor_policy": "Guardian visits in ground floor lounge only",
        "is_verified_by_admin": True,
        "media": [("hotel2", "Twin sharing room"), ("hotel3", "Room interior"), ("living1", "Reception lounge"), ("bathroom", "Bathroom")],
        "rooms": [
            {"name": "Deluxe Twin", "type": "SHARED", "rent": 18000, "deposit": 18000, "bath": True, "balcony": False, "ac": True, "furnished": True, "capacity": 2,
             "seats": [("Bed 1", 18000, False), ("Bed 2", 18000, True)]},
            {"name": "Premium Twin", "type": "SHARED", "rent": 21000, "deposit": 21000, "bath": True, "balcony": True, "ac": True, "furnished": True, "capacity": 2,
             "seats": [("Bed 1", 21000, False), ("Bed 2", 21000, False)]},
        ],
    },
    {
        "title": "Student Hostel Near IUB Campus, Badda",
        "description": "Male student hostel five minutes from Independent University Bangladesh. Four-seat dorms and two-seat private rooms, study table for every seat and high-speed fiber WiFi. Meal plan optional.",
        "property_type": "HOSTEL",
        "address_line": "Plot 9, Block E, Bashundhara Badda Link Road",
        "area_neighborhood": "Badda",
        "latitude": 23.7957,
        "longitude": 90.4356,
        "total_floors": 6,
        "floor_number": 4,
        "has_lift": True,
        "has_generator": True,
        "has_cctv": True,
        "has_wifi": True,
        "gate_closing_time": "12:00 AM",
        "visitor_policy": "Visitors allowed until 8 PM",
        "is_verified_by_admin": False,
        "media": [("bunk", "Dorm room"), ("hotel1", "Private room"), ("interior1", "Study lounge")],
        "rooms": [
            {"name": "Dorm 1", "type": "SHARED", "rent": 6500, "deposit": 6500, "bath": True, "balcony": False, "ac": False, "furnished": True, "capacity": 4,
             "seats": [("Bed 1", 6500, False), ("Bed 2", 6500, True), ("Bed 3", 6500, False), ("Bed 4", 6500, False)]},
            {"name": "Private Twin", "type": "SHARED", "rent": 9000, "deposit": 9000, "bath": True, "balcony": True, "ac": True, "furnished": True, "capacity": 2,
             "seats": [("Bed 1", 9000, False), ("Bed 2", 9000, False)]},
        ],
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == OWNER_EMAIL))
        owner = result.scalar_one()

        result = await db.execute(select(Property).where(Property.owner_id == owner.id))
        for existing in result.scalars().all():
            await db.delete(existing)
        await db.flush()

        rooms_count = 0
        seats_count = 0
        media_count = 0
        for entry in PROPERTIES:
            prop = Property(
                owner_id=owner.id,
                title=entry["title"],
                description=entry["description"],
                property_type=entry["property_type"],
                address_line=entry["address_line"],
                area_neighborhood=entry["area_neighborhood"],
                city="Dhaka",
                latitude=entry["latitude"],
                longitude=entry["longitude"],
                total_floors=entry.get("total_floors"),
                floor_number=entry.get("floor_number"),
                flat_number=entry.get("flat_number"),
                has_lift=entry["has_lift"],
                has_generator=entry["has_generator"],
                has_cctv=entry["has_cctv"],
                has_wifi=entry["has_wifi"],
                gate_closing_time=entry.get("gate_closing_time"),
                visitor_policy=entry.get("visitor_policy"),
                is_published=True,
                is_verified_by_admin=entry["is_verified_by_admin"],
            )
            db.add(prop)
            await db.flush()

            for order, (key, caption) in enumerate(entry["media"]):
                db.add(PropertyMedia(
                    property_id=prop.id,
                    media_url=img(key),
                    media_type="IMAGE",
                    caption=caption,
                    is_cover=(order == 0),
                    display_order=order,
                ))
                media_count += 1

            for room_entry in entry["rooms"]:
                occupied = sum(1 for seat in room_entry.get("seats", []) if seat[2])
                room = Room(
                    property_id=prop.id,
                    room_number_or_name=room_entry["name"],
                    room_type=room_entry["type"],
                    monthly_rent=room_entry["rent"],
                    security_deposit=room_entry["deposit"],
                    has_attached_bathroom=room_entry["bath"],
                    has_balcony=room_entry["balcony"],
                    has_ac=room_entry["ac"],
                    is_furnished=room_entry["furnished"],
                    total_capacity=room_entry["capacity"],
                    current_occupancy=occupied,
                )
                db.add(room)
                await db.flush()
                rooms_count += 1

                for seat_identifier, seat_rent, is_occupied in room_entry.get("seats", []):
                    db.add(RoomSeat(
                        room_id=room.id,
                        seat_identifier=seat_identifier,
                        monthly_rent=seat_rent,
                        is_occupied=is_occupied,
                    ))
                    seats_count += 1

        await db.commit()
        print(f"seeded {len(PROPERTIES)} properties, {rooms_count} rooms, {seats_count} seats, {media_count} media for {OWNER_EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
