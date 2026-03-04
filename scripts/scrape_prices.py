"""
Scrape competitor prices for all tracked listings.

Runs as part of the 3x/day GitHub Actions pipeline.
"""

import asyncio
from datetime import date

from core.constants import BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM
from core.logging import logger
from infrastructure.database.session import async_session, engine
from infrastructure.database.models import Base, CompetitorPriceModel
from infrastructure.database.repository import ListingRepository, CompetitorPriceRepository
from infrastructure.scraping.airbnb_scraper import AirbnbScraper
from infrastructure.scraping.booking_scraper import BookingScraper


async def scrape_prices() -> None:
    """Scrape current prices for all tracked listings."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        listing_repo = ListingRepository(session)
        price_repo = CompetitorPriceRepository(session)

        all_listings = await listing_repo.get_all()
        today = date.today()

        # Group by platform
        airbnb_ids = [l.external_id for l in all_listings if l.platform == "airbnb"]
        booking_ids = [l.external_id for l in all_listings if l.platform == "booking"]
        id_map = {l.external_id: l.id for l in all_listings}

        total = 0

        # Scrape Airbnb prices
        if airbnb_ids:
            scraper = AirbnbScraper(BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM)
            try:
                prices = await scraper.scrape_prices(airbnb_ids)
                for p in prices:
                    listing_id = id_map.get(p.get("external_id"))
                    if listing_id:
                        price_record = CompetitorPriceModel(
                            listing_id=listing_id,
                            date=today,
                            price=p.get("price", 0.0),
                            is_available=p.get("is_available", True),
                        )
                        await price_repo.create(price_record)
                        total += 1
            except Exception as e:
                logger.error("Airbnb price scrape failed: %s", e)

        # Scrape Booking.com prices
        if booking_ids:
            scraper = BookingScraper(BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM)
            try:
                prices = await scraper.scrape_prices(booking_ids)
                for p in prices:
                    listing_id = id_map.get(p.get("external_id"))
                    if listing_id:
                        price_record = CompetitorPriceModel(
                            listing_id=listing_id,
                            date=today,
                            price=p.get("price", 0.0),
                            is_available=p.get("is_available", True),
                        )
                        await price_repo.create(price_record)
                        total += 1
            except Exception as e:
                logger.error("Booking.com price scrape failed: %s", e)

        logger.info("Price scrape complete: %d price records created", total)


if __name__ == "__main__":
    asyncio.run(scrape_prices())
