from core.logging import logger
from infrastructure.database.repository import (
    CompetitorPriceRepository,
    EventRepository,
    ListingRepository,
    WeatherRepository,
)
from infrastructure.database.session import async_session
from services.demand_service import DemandService
from services.pricing_service import PricingService
from services.similarity_service import SimilarityService


class PriceUpdateWorker:
    async def run(self) -> None:
        logger.info("Starting price update worker")

        async with async_session() as session:
            listing_repo = ListingRepository(session)
            competitor_repo = CompetitorPriceRepository(session)
            event_repo = EventRepository(session)
            weather_repo = WeatherRepository(session)

            similarity_service = SimilarityService(listing_repo)
            demand_service = DemandService(event_repo, weather_repo, competitor_repo)
            pricing_service = PricingService(listing_repo, competitor_repo)

            listings = await listing_repo.get_all()
            logger.info("Processing %d listings for price updates", len(listings))

            for listing in listings:
                similar_ids = await similarity_service.find_similar(listing.id)

                from datetime import date
                demand_index = await demand_service.compute_demand_index(
                    target_date=date.today(),
                    location=listing.location,
                    listing_ids=similar_ids,
                )

                recommended_price = await pricing_service.calculate_price(
                    listing_id=listing.id,
                    demand_index=demand_index,
                    similar_listing_ids=similar_ids,
                )

                logger.info(
                    "Listing %d: demand=%.3f, recommended_price=%.2f",
                    listing.id, demand_index, recommended_price,
                )

        logger.info("Price update worker completed")
