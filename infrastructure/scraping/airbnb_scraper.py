from dataclasses import dataclass
from core.logging import logger


@dataclass
class ScrapedListing:
    external_id: str
    platform: str
    title: str
    location: str
    lat: float
    lng: float
    capacity: int
    bedrooms: int
    bathrooms: int
    square_meters: float
    rating: float
    review_count: int
    amenities: list[str]
    base_price: float


class AirbnbScraper:
    def __init__(self, center_lat: float, center_lng: float, radius_km: float):
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.radius_km = radius_km

    async def scrape_listings(self) -> list[ScrapedListing]:
        logger.info(
            "Scraping Airbnb listings around (%.4f, %.4f) radius %.1f km",
            self.center_lat, self.center_lng, self.radius_km,
        )
        # TODO: Implement actual Airbnb scraping logic
        return []

    async def scrape_prices(self, listing_ids: list[str]) -> list[dict]:
        logger.info("Scraping Airbnb prices for %d listings", len(listing_ids))
        # TODO: Implement actual price scraping logic
        return []
