from dataclasses import dataclass
from datetime import date


@dataclass
class Event:
    event_name: str
    location: str
    date: date
    impact_score: float
    id: int | None = None
