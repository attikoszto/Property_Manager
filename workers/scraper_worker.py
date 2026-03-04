from core.logging import logger
from core.settings import settings
from infrastructure.scraping.airbnb_scraper import AirbnbScraper
from infrastructure.scraping.booking_scraper import BookingScraper
from infrastructure.database.session import async_session
from infrastructure.database.repository import ListingRepository, CompetitorPriceRepository
from infrastructure.database.models import ListingModel, CompetitorPriceModel


class ScraperWorker:
    def __init__(self):
        self.airbnb = AirbnbScraper(
            center_lat=settings.region_center_lat,
            center_lng=settings.region_center_lng,
            radius_km=settings.region_radius_km,
        )
        self.booking = BookingScraper(
            center_lat=settings.region_center_lat,
            center_lng=settings.region_center_lng,
            radius_km=settings.region_radius_km,
        )

    async def run(self) -> None:
        logger.info("Starting scraper worker")

        async with async_session() as session:
            listing_repo = ListingRepository(session)
            competitor_repo = CompetitorPriceRepository(session)

            await self._scrape_platform(self.airbnb, listing_repo, competitor_repo)
            await self._scrape_platform(self.booking, listing_repo, competitor_repo)

        logger.info("Scraper worker completed")

    async def _scrape_platform(self, scraper, listing_repo, competitor_repo) -> None:
        listings = await scraper.scrape_listings()
        logger.info("Scraped %d listings from %s", len(listings), type(scraper).__name__)

        for scraped in listings:
            listing_model = ListingModel(
                external_id=scraped.external_id,
                platform=scraped.platform,
                title=scraped.title,
                location=scraped.location,
                lat=scraped.lat,
                lng=scraped.lng,
                capacity=scraped.capacity,
                bedrooms=scraped.bedrooms,
                bathrooms=scraped.bathrooms,
                square_meters=scraped.square_meters,
                rating=scraped.rating,
                review_count=scraped.review_count,
                amenities=scraped.amenities,
                base_price=scraped.base_price,
            )
            await listing_repo.upsert(listing_model)
