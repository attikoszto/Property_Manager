from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Booking:
    listing_id: int
    checkin_date: date
    checkout_date: date
    price: float
    channel: str
    id: int | None = None
    booked_at: datetime = field(default_factory=datetime.utcnow)
