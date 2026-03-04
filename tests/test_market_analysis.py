"""Tests for MarketAnalysisService – momentum, shock, saturation, shadow pricing."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

from services.market_analysis_service import MarketAnalysisService


class TestMarketAnalysisService:
    def setup_method(self):
        self.market_repo = MagicMock()
        self.search_repo = MagicMock()
        self.flight_repo = MagicMock()
        self.service = MarketAnalysisService(
            market_repo=self.market_repo,
            search_repo=self.search_repo,
            flight_repo=self.flight_repo,
        )

    def _make_snapshot(self, occ=0.6, velocity=5.0, median_price=150.0, total=100, available=40):
        s = MagicMock()
        s.avg_occupancy_rate = occ
        s.booking_velocity = velocity
        s.median_price = median_price
        s.total_listings = total
        s.available_listings = available
        return s

    async def test_demand_momentum_increasing(self):
        snapshots = [
            self._make_snapshot(occ=0.50, velocity=3.0, median_price=140.0),
            self._make_snapshot(occ=0.55, velocity=4.0, median_price=145.0),
            self._make_snapshot(occ=0.60, velocity=5.0, median_price=150.0),
            self._make_snapshot(occ=0.62, velocity=5.5, median_price=152.0),
            self._make_snapshot(occ=0.65, velocity=6.0, median_price=155.0),
            self._make_snapshot(occ=0.68, velocity=7.0, median_price=158.0),
            self._make_snapshot(occ=0.72, velocity=8.0, median_price=162.0),
        ]
        self.market_repo.get_trend = AsyncMock(return_value=snapshots)

        momentum = await self.service.compute_demand_momentum("Berchtesgaden")

        assert momentum.occupancy_trend_7_days > 0
        assert momentum.momentum_increasing is True

    async def test_demand_momentum_no_data(self):
        self.market_repo.get_trend = AsyncMock(return_value=[])

        momentum = await self.service.compute_demand_momentum("Berchtesgaden")

        assert momentum.occupancy_trend_3_days == 0.0
        assert momentum.momentum_increasing is False

    async def test_demand_shock_detected(self):
        snapshots = [
            self._make_snapshot(occ=0.50, velocity=3.0),
            self._make_snapshot(occ=0.75, velocity=8.0),  # big jump
        ]
        self.market_repo.get_trend = AsyncMock(return_value=snapshots)

        shock = await self.service.detect_demand_shock("Berchtesgaden")

        assert shock.demand_shock is True
        assert shock.shock_direction == "up"

    async def test_demand_shock_not_detected(self):
        snapshots = [
            self._make_snapshot(occ=0.60, velocity=5.0),
            self._make_snapshot(occ=0.62, velocity=5.2),  # small change
        ]
        self.market_repo.get_trend = AsyncMock(return_value=snapshots)

        shock = await self.service.detect_demand_shock("Berchtesgaden")

        assert shock.demand_shock is False

    async def test_market_saturation_oversupply(self):
        snapshot = self._make_snapshot(total=100, available=80)
        self.market_repo.get_latest = AsyncMock(return_value=snapshot)

        sat = await self.service.compute_market_saturation("Berchtesgaden")

        assert sat.available_listings_ratio == 0.8
        assert sat.pricing_power == "low"

    async def test_market_saturation_undersupply(self):
        snapshot = self._make_snapshot(total=100, available=20)
        self.market_repo.get_latest = AsyncMock(return_value=snapshot)

        sat = await self.service.compute_market_saturation("Berchtesgaden")

        assert sat.available_listings_ratio == 0.2
        assert sat.pricing_power == "high"

    async def test_shadow_price_above_market(self):
        snapshot = self._make_snapshot(median_price=100.0)
        self.market_repo.get_latest = AsyncMock(return_value=snapshot)

        estimate = await self.service.estimate_shadow_price(150.0, "Berchtesgaden")

        assert estimate.price_gap_ratio == 1.5
        assert estimate.estimated_elasticity == "elastic"

    async def test_shadow_price_below_market(self):
        snapshot = self._make_snapshot(median_price=200.0)
        self.market_repo.get_latest = AsyncMock(return_value=snapshot)

        estimate = await self.service.estimate_shadow_price(120.0, "Berchtesgaden")

        assert estimate.price_gap_ratio == 0.6
        assert estimate.estimated_elasticity == "inelastic"

    async def test_search_demand_signal(self):
        latest = MagicMock()
        latest.search_interest_index = 75.0
        latest.search_interest_trend = 5.0
        self.search_repo.get_latest = AsyncMock(return_value=latest)

        signal = await self.service.get_search_demand("berchtesgaden skiurlaub", "Berchtesgaden")

        assert signal.search_interest_index == 75.0
        assert signal.demand_increasing is True

    async def test_flight_demand_signal(self):
        latest = MagicMock()
        latest.average_price = 89.0
        latest.price_trend = -5.0
        self.flight_repo.get_latest = AsyncMock(return_value=latest)

        signal = await self.service.get_flight_demand("MUC", "SZG", date(2026, 7, 15))

        assert signal.average_flight_price == 89.0
        assert signal.flights_getting_cheaper is True
