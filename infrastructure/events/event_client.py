from dataclasses import dataclass
from datetime import date

from core.logging import logger


@dataclass
class EventData:
    event_name: str
    location: str
    date: date
    impact_score: float


class EventClient:
    async def get_upcoming_events(self, location: str, days_ahead: int = 30) -> list[EventData]:
        logger.info("Fetching upcoming events for %s (next %d days)", location, days_ahead)
        # TODO: Integrate with event API or local data source
        return []
