"""
Seed the database with sample data for development and testing.
"""

import asyncio
from datetime import date, datetime

from infrastructure.database.session import async_session, engine
from infrastructure.database.models import (
    Base,
    ListingModel,
    CompetitorPriceModel,
    WeatherModel,
    EventModel,
    CleanerModel,
    PropertyCleanerModel,
)
from core.logging import logger


SAMPLE_LISTINGS = [
    {
        "external_id": "airbnb_001",
        "platform": "airbnb",
        "title": "Cozy Alpine Chalet near Königssee",
        "location": "Berchtesgaden",
        "lat": 47.6310,
        "lng": 13.0020,
        "capacity": 4,
        "bedrooms": 2,
        "bathrooms": 1,
        "square_meters": 65.0,
        "rating": 4.8,
        "review_count": 124,
        "amenities": ["wifi", "parking", "kitchen", "balcony"],
        "base_price": 120.0,
        "owner_id": "owner_001",
        "is_customer": True,
    },
    {
        "external_id": "airbnb_002",
        "platform": "airbnb",
        "title": "Mountain View Apartment Berchtesgaden",
        "location": "Berchtesgaden",
        "lat": 47.6325,
        "lng": 13.0065,
        "capacity": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "square_meters": 42.0,
        "rating": 4.5,
        "review_count": 67,
        "amenities": ["wifi", "kitchen", "washer"],
        "base_price": 85.0,
        "owner_id": "owner_002",
        "is_customer": False,
    },
    {
        "external_id": "booking_001",
        "platform": "booking",
        "title": "Luxury Ski Lodge with Sauna",
        "location": "Berchtesgaden",
        "lat": 47.6280,
        "lng": 13.0100,
        "capacity": 8,
        "bedrooms": 4,
        "bathrooms": 2,
        "square_meters": 140.0,
        "rating": 4.9,
        "review_count": 203,
        "amenities": ["wifi", "parking", "sauna", "balcony", "kitchen", "washer"],
        "base_price": 280.0,
        "owner_id": "owner_003",
        "is_customer": False,
    },
    {
        "external_id": "airbnb_003",
        "platform": "airbnb",
        "title": "Charming Studio in Old Town",
        "location": "Berchtesgaden",
        "lat": 47.6318,
        "lng": 13.0035,
        "capacity": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "square_meters": 30.0,
        "rating": 4.3,
        "review_count": 41,
        "amenities": ["wifi", "kitchen"],
        "base_price": 65.0,
        "owner_id": "owner_004",
        "is_customer": False,
    },
    {
        "external_id": "booking_002",
        "platform": "booking",
        "title": "Family House with Garden",
        "location": "Berchtesgaden",
        "lat": 47.6290,
        "lng": 12.9980,
        "capacity": 6,
        "bedrooms": 3,
        "bathrooms": 2,
        "square_meters": 110.0,
        "rating": 4.7,
        "review_count": 89,
        "amenities": ["wifi", "parking", "kitchen", "washer", "balcony"],
        "base_price": 195.0,
        "owner_id": "owner_001",
        "is_customer": True,
    },
]

SAMPLE_EVENTS = [
    {"event_name": "Berchtesgadener Advent", "location": "Berchtesgaden", "date": date(2026, 12, 5), "impact_score": 3.0},
    {"event_name": "Almabtrieb Festival", "location": "Berchtesgaden", "date": date(2026, 9, 20), "impact_score": 2.5},
    {"event_name": "Königssee Summer Festival", "location": "Berchtesgaden", "date": date(2026, 7, 15), "impact_score": 2.0},
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        for data in SAMPLE_LISTINGS:
            listing = ListingModel(**data)
            session.add(listing)
        await session.commit()
        logger.info("Seeded %d listings", len(SAMPLE_LISTINGS))

        for data in SAMPLE_EVENTS:
            event = EventModel(**data)
            session.add(event)
        await session.commit()
        logger.info("Seeded %d events", len(SAMPLE_EVENTS))

        cleaner = CleanerModel(
            name="Maria Huber",
            phone="+49 170 1234567",
            email="maria@example.com",
            availability_schedule={"monday": ["09:00-17:00"], "tuesday": ["09:00-17:00"]},
        )
        session.add(cleaner)
        await session.commit()
        logger.info("Seeded sample cleaner")

    logger.info("Database seeding complete")


if __name__ == "__main__":
    asyncio.run(seed())
