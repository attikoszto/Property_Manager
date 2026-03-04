"""
API routes for advanced demand signals and market analysis.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.dependencies import (
    get_market_analysis_service,
    get_weather_feature_service,
)
from services.market_analysis_service import MarketAnalysisService
from services.weather_feature_service import WeatherFeatureService

router = APIRouter()


# --- Response Models ---

class WeatherSignalsResponse(BaseModel):
    stay_date: date
    ski_condition_index: float
    outdoor_condition_index: float
    sun_after_snow: bool
    demand_spike_probability: float


class DemandMomentumResponse(BaseModel):
    occupancy_trend_3_days: float
    occupancy_trend_7_days: float
    booking_velocity_trend: float
    market_price_trend: float
    momentum_increasing: bool


class DemandShockResponse(BaseModel):
    demand_shock: bool
    shock_magnitude: float
    shock_direction: str


class MarketSaturationResponse(BaseModel):
    available_listings_ratio: float
    pricing_power: str


class ShadowPriceResponse(BaseModel):
    system_price: float
    market_median_price: float
    price_gap_ratio: float
    estimated_elasticity: str


class SearchDemandResponse(BaseModel):
    search_interest_index: float
    search_interest_trend: float
    demand_increasing: bool


class FlightDemandResponse(BaseModel):
    average_flight_price: float
    flight_price_trend: float
    flights_getting_cheaper: bool


class FullDemandSignalsResponse(BaseModel):
    """Combined response with all demand signals for a stay date."""
    weather: WeatherSignalsResponse
    momentum: DemandMomentumResponse
    shock: DemandShockResponse
    saturation: MarketSaturationResponse
    search: SearchDemandResponse


# --- Endpoints ---

@router.get("/weather-signals", response_model=WeatherSignalsResponse)
async def get_weather_signals(
    stay_date: date = Query(...),
    location: str = Query(default="Berchtesgaden"),
    service: WeatherFeatureService = Depends(get_weather_feature_service),
):
    """Get ski/outdoor condition indices and weather-based demand signals."""
    signals = await service.compute_signals(stay_date, location)
    return WeatherSignalsResponse(
        stay_date=stay_date,
        ski_condition_index=signals.ski_condition_index,
        outdoor_condition_index=signals.outdoor_condition_index,
        sun_after_snow=signals.sun_after_snow,
        demand_spike_probability=signals.demand_spike_probability,
    )


@router.get("/momentum", response_model=DemandMomentumResponse)
async def get_demand_momentum(
    location: str = Query(default="Berchtesgaden"),
    service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Get demand momentum trends over 3-day and 7-day windows."""
    momentum = await service.compute_demand_momentum(location)
    return DemandMomentumResponse(
        occupancy_trend_3_days=momentum.occupancy_trend_3_days,
        occupancy_trend_7_days=momentum.occupancy_trend_7_days,
        booking_velocity_trend=momentum.booking_velocity_trend,
        market_price_trend=momentum.market_price_trend,
        momentum_increasing=momentum.momentum_increasing,
    )


@router.get("/shock", response_model=DemandShockResponse)
async def get_demand_shock(
    location: str = Query(default="Berchtesgaden"),
    threshold: float = Query(default=0.15),
    service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Detect sudden demand spikes or drops."""
    shock = await service.detect_demand_shock(location, threshold)
    return DemandShockResponse(
        demand_shock=shock.demand_shock,
        shock_magnitude=shock.shock_magnitude,
        shock_direction=shock.shock_direction,
    )


@router.get("/saturation", response_model=MarketSaturationResponse)
async def get_market_saturation(
    location: str = Query(default="Berchtesgaden"),
    service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Get market supply/demand balance metrics."""
    sat = await service.compute_market_saturation(location)
    return MarketSaturationResponse(
        available_listings_ratio=sat.available_listings_ratio,
        pricing_power=sat.pricing_power,
    )


@router.get("/shadow-price", response_model=ShadowPriceResponse)
async def get_shadow_price(
    system_price: float = Query(...),
    location: str = Query(default="Berchtesgaden"),
    service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Estimate demand elasticity via shadow price comparison."""
    estimate = await service.estimate_shadow_price(system_price, location)
    return ShadowPriceResponse(
        system_price=estimate.system_price,
        market_median_price=estimate.market_median_price,
        price_gap_ratio=estimate.price_gap_ratio,
        estimated_elasticity=estimate.estimated_elasticity,
    )


@router.get("/search", response_model=SearchDemandResponse)
async def get_search_demand(
    query_term: str = Query(default="berchtesgaden skiurlaub"),
    location: str = Query(default="Berchtesgaden"),
    service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Get forward-looking search interest signals."""
    signal = await service.get_search_demand(query_term, location)
    return SearchDemandResponse(
        search_interest_index=signal.search_interest_index,
        search_interest_trend=signal.search_interest_trend,
        demand_increasing=signal.demand_increasing,
    )


@router.get("/flights", response_model=FlightDemandResponse)
async def get_flight_demand(
    origin: str = Query(default="MUC"),
    destination: str = Query(default="SZG"),
    travel_date: date = Query(default_factory=date.today),
    service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Get flight price signals affecting tourism demand."""
    signal = await service.get_flight_demand(origin, destination, travel_date)
    return FlightDemandResponse(
        average_flight_price=signal.average_flight_price,
        flight_price_trend=signal.flight_price_trend,
        flights_getting_cheaper=signal.flights_getting_cheaper,
    )


@router.get("/full", response_model=FullDemandSignalsResponse)
async def get_full_demand_signals(
    stay_date: date = Query(...),
    location: str = Query(default="Berchtesgaden"),
    weather_service: WeatherFeatureService = Depends(get_weather_feature_service),
    market_service: MarketAnalysisService = Depends(get_market_analysis_service),
):
    """Get all demand signals combined for a stay date."""
    weather = await weather_service.compute_signals(stay_date, location)
    momentum = await market_service.compute_demand_momentum(location)
    shock = await market_service.detect_demand_shock(location)
    saturation = await market_service.compute_market_saturation(location)
    search = await market_service.get_search_demand("berchtesgaden skiurlaub", location)

    return FullDemandSignalsResponse(
        weather=WeatherSignalsResponse(
            stay_date=stay_date,
            ski_condition_index=weather.ski_condition_index,
            outdoor_condition_index=weather.outdoor_condition_index,
            sun_after_snow=weather.sun_after_snow,
            demand_spike_probability=weather.demand_spike_probability,
        ),
        momentum=DemandMomentumResponse(
            occupancy_trend_3_days=momentum.occupancy_trend_3_days,
            occupancy_trend_7_days=momentum.occupancy_trend_7_days,
            booking_velocity_trend=momentum.booking_velocity_trend,
            market_price_trend=momentum.market_price_trend,
            momentum_increasing=momentum.momentum_increasing,
        ),
        shock=DemandShockResponse(
            demand_shock=shock.demand_shock,
            shock_magnitude=shock.shock_magnitude,
            shock_direction=shock.shock_direction,
        ),
        saturation=MarketSaturationResponse(
            available_listings_ratio=saturation.available_listings_ratio,
            pricing_power=saturation.pricing_power,
        ),
        search=SearchDemandResponse(
            search_interest_index=search.search_interest_index,
            search_interest_trend=search.search_interest_trend,
            demand_increasing=search.demand_increasing,
        ),
    )
