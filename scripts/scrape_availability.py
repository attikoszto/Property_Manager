"""
Scrape availability snapshots for all tracked listings.

Runs as part of the 3x/day GitHub Actions pipeline.
Detects bookings by comparing availability changes between snapshots.
"""

import asyncio
from datetime import date

from core.constants import BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM
from core.logging import logger
from infrastructure.database.session import async_session, engine
from infrastructure.database.models import Base
from infrastructure.database.repository import (
    ListingRepository,
    AvailabilityRepository,
    MarketSnapshotRepository,
)
from infrastructure.database.models import MarketSnapshotModel


async def scrape_availability() -> None:
    """Check availability for all listings and record snapshots.

    After recording, detect likely bookings and create a market snapshot.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        listing_repo = ListingRepository(session)
        avail_repo = AvailabilityRepository(session)
        market_repo = MarketSnapshotRepository(session)

        all_listings = await listing_repo.get_all()
        today = date.today()
        total = 0
        available_count = 0

        for listing in all_listings:
            try:
                # TODO: Replace with actual availability check via scraping
                # For now, record a placeholder; real implementation will
                # fetch calendar data from platform APIs
                is_available = True  # placeholder
                await avail_repo.record_snapshot(listing.id, today, is_available)
                total += 1
                if is_available:
                    available_count += 1
            except Exception as e:
                logger.error("Availability check failed for listing %d: %s", listing.id, e)

        # Detect bookings from availability transitions
        likely_bookings = await avail_repo.detect_bookings(today)
        if likely_bookings:
            logger.info("Detected %d likely bookings", len(likely_bookings))

        # Compute market occupancy
        occupancy = await avail_repo.compute_market_occupancy(today)

        # Record market snapshot
        if total > 0:
            snapshot = MarketSnapshotModel(
                date=today,
                location="Berchtesgaden",
                total_listings=total,
                available_listings=available_count,
                median_price=0.0,  # updated by price scraper
                avg_occupancy_rate=occupancy,
                booking_velocity=float(len(likely_bookings)),
            )
            await market_repo.create(snapshot)

        logger.info(
            "Availability scrape complete: %d listings, %.1f%% occupied, %d new bookings",
            total,
            occupancy * 100,
            len(likely_bookings),
        )


if __name__ == "__main__":
    asyncio.run(scrape_availability())
