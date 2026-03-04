"""Shared domain objects for scraping infrastructure."""

import re
from dataclasses import dataclass, field

# ---- property-type classification rules ----
_TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"\b(hotel|gasthof|pension|inn\b|motel)", "hotel"),
    (r"\b(hostel|jugendherberge|backpacker)", "hostel"),
    (r"\b(apartment|wohnung|ferienwohnung|apt\b|studio)", "apartment"),
    (r"\b(cabin|h[uü]tte|chalet|lodge|blockhaus)", "cabin"),
    (r"\b(villa|haus|house|home|cottage|bungalow|farmhouse|bauernhof)", "house"),
    (r"\b(room|zimmer|privatzimmer)", "room"),
    (r"\b(entire|place to stay|place in)", "apartment"),
]


def classify_property_type(title: str, *, platform_hint: str = "") -> str:
    """Classify a listing into a property type based on its title.

    Returns one of: hotel, hostel, apartment, cabin, house, room, unknown.
    """
    t = title.lower()
    for pattern, ptype in _TYPE_PATTERNS:
        if re.search(pattern, t, re.I):
            return ptype
    # Airbnb labels like "Entire rental unit" → apartment
    if "entire" in t and ("rental" in t or "unit" in t or "condo" in t):
        return "apartment"
    return "unknown"


@dataclass
class ScrapedListing:
    """Domain object representing a scraped vacation rental listing.

    Shared across all platform scrapers. Classes handle structure
    and business logic; DataFrames handle analytical computations.
    """

    external_id: str
    platform: str
    property_type: str  # hotel, apartment, vacation_rental, room, hostel, unknown
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
