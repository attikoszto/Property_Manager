from datetime import date
from unittest.mock import AsyncMock, MagicMock

from services.demand_service import DemandService


class TestDemandService:
    def setup_method(self):
        self.event_repo = MagicMock()
        self.weather_repo = MagicMock()
        self.competitor_repo = MagicMock()
        self.service = DemandService(self.event_repo, self.weather_repo, self.competitor_repo)

    def test_season_factor_winter(self):
        factor = self.service.get_season_factor(date(2026, 1, 15))
        assert factor == 1.4

    def test_season_factor_summer(self):
        factor = self.service.get_season_factor(date(2026, 7, 15))
        assert factor == 1.5

    def test_season_factor_november(self):
        factor = self.service.get_season_factor(date(2026, 11, 15))
        assert factor == 0.7

    def test_weekday_factor_saturday(self):
        saturday = date(2026, 3, 7)
        factor = self.service.get_weekday_factor(saturday)
        assert factor == 1.2

    def test_weekday_factor_monday(self):
        monday = date(2026, 3, 2)
        factor = self.service.get_weekday_factor(monday)
        assert factor == 0.9

    async def test_event_factor_no_events(self):
        self.event_repo.get_events_for_date = AsyncMock(return_value=[])
        factor = await self.service.get_event_factor(date(2026, 3, 4), "Berchtesgaden")
        assert factor == 1.0

    async def test_event_factor_with_event(self):
        event = MagicMock()
        event.impact_score = 3.0
        self.event_repo.get_events_for_date = AsyncMock(return_value=[event])
        factor = await self.service.get_event_factor(date(2026, 12, 5), "Berchtesgaden")
        assert factor == 1.6

    async def test_compute_demand_index(self):
        self.event_repo.get_events_for_date = AsyncMock(return_value=[])
        self.weather_repo.get_weather = AsyncMock(return_value=None)
        self.competitor_repo.get_availability_count = AsyncMock(return_value=5)

        index = await self.service.compute_demand_index(
            target_date=date(2026, 7, 15),
            location="Berchtesgaden",
            listing_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        )

        assert index > 0
        assert isinstance(index, float)
