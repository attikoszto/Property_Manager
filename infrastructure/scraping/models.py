"""Shared domain objects for scraping infrastructure."""

from dataclasses import dataclass, field


@dataclass
class ScrapedListing:
    """Domain object representing a scraped vacation rental listing.

    Shared across all platform scrapers. Classes handle structure
    and business logic; DataFrames handle analytical computations.
    """

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
    amenities: list[str] = field(default_factory=list)
    base_price: float = 0.0


@dataclass
class ScrapedPrice:
    """Domain object representing a scraped price point."""

    external_id: str
    price: float
    is_available: bool = True
    currency: str = "EUR"
