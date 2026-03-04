from datetime import date

from core.constants import SEASONALITY_FACTORS, WEEKDAY_FACTORS
from infrastructure.database.repository import (
    EventRepository,
    WeatherRepository,
    CompetitorPriceRepository,
)


class DemandService:
    def __init__(
        self,
        event_repo: EventRepository,
        weather_repo: WeatherRepository,
        competitor_repo: CompetitorPriceRepository,
    ):
        self.event_repo = event_repo
        self.weather_repo = weather_repo
        self.competitor_repo = competitor_repo

    def get_season_factor(self, target_date: date) -> float:
        return SEASONALITY_FACTORS.get(target_date.month, 1.0)

    def get_weekday_factor(self, target_date: date) -> float:
        return WEEKDAY_FACTORS.get(target_date.weekday(), 1.0)

    async def get_event_factor(self, target_date: date, location: str) -> float:
        events = await self.event_repo.get_events_for_date(target_date, location)
        if not events:
            return 1.0
        max_impact = max(e.impact_score for e in events)
        return 1.0 + max_impact * 0.2

    async def get_weather_factor(self, target_date: date, location: str) -> float:
        weather = await self.weather_repo.get_weather(target_date, location)
        if not weather:
            return 1.0
        if weather.snow_probability > 0.5:
            return 1.1
        if weather.rain_probability > 0.7:
            return 0.9
        return 1.0

    async def get_occupancy_factor(self, listing_ids: list[int], target_date: date) -> float:
        if not listing_ids:
            return 1.0
        available = await self.competitor_repo.get_availability_count(listing_ids, target_date)
        total = len(listing_ids)
        occupancy_rate = 1.0 - (available / total) if total > 0 else 0.5
        return 0.8 + occupancy_rate * 0.4

    async def compute_demand_index(
        self,
        target_date: date,
        location: str,
        listing_ids: list[int],
    ) -> float:
        season = self.get_season_factor(target_date)
        weekday = self.get_weekday_factor(target_date)
        event = await self.get_event_factor(target_date, location)
        weather = await self.get_weather_factor(target_date, location)
        occupancy = await self.get_occupancy_factor(listing_ids, target_date)

        return round(season * weekday * event * weather * occupancy, 4)
