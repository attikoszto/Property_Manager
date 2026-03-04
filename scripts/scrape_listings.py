"""
Scrape listings from Airbnb and Booking.com platforms.

Runs as part of the daily data pipeline (1x/day recommended).
Uses Playwright headless browser to bypass anti-bot protections.

IMPORTANT: This scraper is for personal market-research purposes.
Rate limits and delays are built in to behave like a normal user.
"""

import asyncio
import random

from core.constants import BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM
from core.logging import logger
from infrastructure.database.models import Base, ListingModel
from infrastructure.database.repository import ListingRepository
from infrastructure.database.session import async_session, engine
from infrastructure.scraping.airbnb_scraper import AirbnbScraper
from infrastructure.scraping.booking_scraper import BookingScraper


async def scrape_listings() -> None:
    """Scrape listings from all platforms and upsert into the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scrapers = [
        AirbnbScraper(BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM),
        BookingScraper(BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM),
    ]

    async with async_session() as session:
        repo = ListingRepository(session)
        total = 0

        for i, scraper in enumerate(scrapers):
            # Random delay between platforms to avoid correlated requests
            if i > 0:
                delay = random.uniform(10, 25)
                logger.info("Waiting %.0fs before next platform…", delay)
                await asyncio.sleep(delay)

            try:
                scraped = await scraper.scrape_listings()
                for item in scraped:
                    listing = ListingModel(
                        external_id=item.external_id,
                        platform=item.platform,
                        title=item.title,
                        location=item.location,
                        lat=item.lat,
                        lng=item.lng,
                        capacity=item.capacity,
                        bedrooms=item.bedrooms,
                        bathrooms=item.bathrooms,
                        square_meters=item.square_meters,
                        rating=item.rating,
                        review_count=item.review_count,
                        amenities=item.amenities,
                        base_price=item.base_price,
                    )
                    await repo.upsert(listing)
                    total += 1
                logger.info(
                    "Scraped %d listings from %s",
                    len(scraped),
                    scraper.__class__.__name__,
                )
            except Exception as e:
                logger.error("Scraper %s failed: %s", scraper.__class__.__name__, e)

        logger.info("Listing scrape complete: %d listings processed", total)


if __name__ == "__main__":
    asyncio.run(scrape_listings())
