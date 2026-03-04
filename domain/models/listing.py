from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Listing:
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
    owner_id: str | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
