"""
Market Analysis Service – Demand Momentum, Shock Detection, Saturation, Shadow Pricing.

Computes market-level signals for advanced pricing decisions.
"""

from dataclasses import dataclass
from datetime import date

from infrastructure.database.repository import (
    AvailabilityRepository,
    CompetitorPriceRepository,
    FlightPriceRepository,
    MarketSnapshotRepository,
    SearchDemandRepository,
)


@dataclass
class DemandMomentumSignals:
    """Trend signals over recent time windows."""
    occupancy_trend_3_days: float
    occupancy_trend_7_days: float
    booking_velocity_trend: float
    market_price_trend: float
    momentum_increasing: bool


@dataclass
class DemandShockSignal:
    """Indicates a sudden demand spike or drop."""
    demand_shock: bool
    shock_magnitude: float
    shock_direction: str  # "up" or "down"


@dataclass
class MarketSaturationSignal:
    """Supply/demand balance metrics."""
    available_listings_ratio: float
    pricing_power: str  # "high", "medium", "low"


@dataclass
class ShadowPriceEstimate:
    """Estimate demand elasticity without direct booking data."""
    system_price: float
    market_median_price: float
    price_gap_ratio: float
    estimated_elasticity: str  # "elastic", "inelastic", "neutral"


@dataclass
class SearchDemandSignal:
    """Forward-looking search interest signals."""
    search_interest_index: float
    search_interest_trend: float
    demand_increasing: bool


@dataclass
class FlightDemandSignal:
    """Flight price signals affecting tourism demand."""
    average_flight_price: float
    flight_price_trend: float
    flights_getting_cheaper: bool


class MarketAnalysisService:
    def __init__(
        self,
        market_repo: MarketSnapshotRepository,
        availability_repo: AvailabilityRepository | None = None,
        competitor_repo: CompetitorPriceRepository | None = None,
        search_repo: SearchDemandRepository | None = None,
        flight_repo: FlightPriceRepository | None = None,
    ):
        self.market_repo = market_repo
        self.availability_repo = availability_repo
        self.competitor_repo = competitor_repo
        self.search_repo = search_repo
        self.flight_repo = flight_repo

    async def compute_demand_momentum(
        self, location: str
    ) -> DemandMomentumSignals:
        """Compute demand trend features over 3-day and 7-day windows."""
        snapshots_7d = await self.market_repo.get_trend(location, days=7)
        snapshots_3d = snapshots_7d[-3:] if len(snapshots_7d) >= 3 else snapshots_7d

        def _compute_trend(values: list[float]) -> float:
            if len(values) < 2:
                return 0.0
            return (values[-1] - values[0]) / max(len(values) - 1, 1)

        occ_values_3d = [s.avg_occupancy_rate for s in snapshots_3d]
        occ_values_7d = [s.avg_occupancy_rate for s in snapshots_7d]
        vel_values = [s.booking_velocity for s in snapshots_7d]
        price_values = [s.median_price for s in snapshots_7d]

        occ_trend_3d = _compute_trend(occ_values_3d)
        occ_trend_7d = _compute_trend(occ_values_7d)
        vel_trend = _compute_trend(vel_values)
        price_trend = _compute_trend(price_values)

        momentum_up = occ_trend_7d > 0.01 and vel_trend > 0

        return DemandMomentumSignals(
            occupancy_trend_3_days=round(occ_trend_3d, 4),
            occupancy_trend_7_days=round(occ_trend_7d, 4),
            booking_velocity_trend=round(vel_trend, 4),
            market_price_trend=round(price_trend, 2),
            momentum_increasing=momentum_up,
        )

    async def detect_demand_shock(
        self, location: str, threshold: float = 0.15
    ) -> DemandShockSignal:
        """Detect sudden demand spikes or drops.

        A shock occurs when the occupancy rate or booking velocity
        changes by more than the threshold between consecutive snapshots.
        """
        snapshots = await self.market_repo.get_trend(location, days=3)

        if len(snapshots) < 2:
            return DemandShockSignal(demand_shock=False, shock_magnitude=0.0, shock_direction="up")

        prev = snapshots[-2]
        curr = snapshots[-1]

        occ_change = curr.avg_occupancy_rate - prev.avg_occupancy_rate
        vel_change = (
            (curr.booking_velocity - prev.booking_velocity) / max(prev.booking_velocity, 0.01)
            if prev.booking_velocity > 0
            else 0.0
        )

        magnitude = max(abs(occ_change), abs(vel_change))
        shock = magnitude > threshold
        direction = "up" if occ_change > 0 else "down"

        return DemandShockSignal(
            demand_shock=shock,
            shock_magnitude=round(magnitude, 4),
            shock_direction=direction,
        )

    async def compute_market_saturation(
        self, location: str
    ) -> MarketSaturationSignal:
        """Compute available_listings_ratio to measure supply pressure.

        high ratio → oversupply → lower pricing power
        low ratio → undersupply → higher pricing power
        """
        snapshot = await self.market_repo.get_latest(location)
        if not snapshot or snapshot.total_listings == 0:
            return MarketSaturationSignal(
                available_listings_ratio=0.5, pricing_power="medium"
            )

        ratio = snapshot.available_listings / snapshot.total_listings

        if ratio > 0.7:
            power = "low"
        elif ratio > 0.4:
            power = "medium"
        else:
            power = "high"

        return MarketSaturationSignal(
            available_listings_ratio=round(ratio, 4),
            pricing_power=power,
        )

    async def estimate_shadow_price(
        self,
        system_price: float,
        location: str,
    ) -> ShadowPriceEstimate:
        """Estimate demand elasticity by comparing system price to market median.

        Even without booking data, we can infer price sensitivity
        by observing how quickly cheaper listings get booked.
        """
        snapshot = await self.market_repo.get_latest(location)
        if not snapshot:
            return ShadowPriceEstimate(
                system_price=system_price,
                market_median_price=system_price,
                price_gap_ratio=1.0,
                estimated_elasticity="neutral",
            )

        median = snapshot.median_price
        gap_ratio = system_price / median if median > 0 else 1.0

        if gap_ratio > 1.2:
            elasticity = "elastic"       # priced high above market
        elif gap_ratio < 0.8:
            elasticity = "inelastic"     # priced well below market
        else:
            elasticity = "neutral"

        return ShadowPriceEstimate(
            system_price=system_price,
            market_median_price=median,
            price_gap_ratio=round(gap_ratio, 4),
            estimated_elasticity=elasticity,
        )

    async def get_search_demand(
        self, query_term: str, location: str
    ) -> SearchDemandSignal:
        """Get forward-looking search interest signals."""
        if not self.search_repo:
            return SearchDemandSignal(
                search_interest_index=0.0,
                search_interest_trend=0.0,
                demand_increasing=False,
            )

        latest = await self.search_repo.get_latest(query_term, location)
        if not latest:
            return SearchDemandSignal(
                search_interest_index=0.0,
                search_interest_trend=0.0,
                demand_increasing=False,
            )

        return SearchDemandSignal(
            search_interest_index=latest.search_interest_index,
            search_interest_trend=latest.search_interest_trend,
            demand_increasing=latest.search_interest_trend > 0,
        )

    async def get_flight_demand(
        self, origin: str, destination: str, travel_date: date
    ) -> FlightDemandSignal:
        """Get flight price signals affecting tourism demand."""
        if not self.flight_repo:
            return FlightDemandSignal(
                average_flight_price=0.0,
                flight_price_trend=0.0,
                flights_getting_cheaper=False,
            )

        latest = await self.flight_repo.get_latest(origin, destination, travel_date)
        if not latest:
            return FlightDemandSignal(
                average_flight_price=0.0,
                flight_price_trend=0.0,
                flights_getting_cheaper=False,
            )

        return FlightDemandSignal(
            average_flight_price=latest.average_price,
            flight_price_trend=latest.price_trend,
            flights_getting_cheaper=latest.price_trend < 0,
        )
