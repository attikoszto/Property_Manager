from datetime import date

import numpy as np

from core.constants import SEASONALITY_FACTORS, WEEKDAY_FACTORS


class DemandFeatureBuilder:
    """Build feature vectors for demand and booking probability models."""

    def build(
        self,
        target_date: date,
        event_impact: float,
        weather_temp: float,
        rain_prob: float,
        snow_prob: float,
        occupancy_rate: float,
    ) -> np.ndarray:
        """Build basic demand features (backward-compatible)."""
        season_factor = SEASONALITY_FACTORS.get(target_date.month, 1.0)
        weekday_factor = WEEKDAY_FACTORS.get(target_date.weekday(), 1.0)
        is_weekend = 1.0 if target_date.weekday() >= 4 else 0.0
        day_of_year = target_date.timetuple().tm_yday / 365.0

        return np.array([
            season_factor,
            weekday_factor,
            is_weekend,
            day_of_year,
            event_impact,
            weather_temp,
            rain_prob,
            snow_prob,
            occupancy_rate,
        ])

    def build_extended(
        self,
        target_date: date,
        days_to_checkin: int,
        event_impact: float,
        temperature_forecast: float,
        rain_probability: float,
        snow_depth: float,
        ski_condition_index: float,
        outdoor_condition_index: float,
        sun_after_snow: bool,
        market_occupancy: float,
        demand_momentum: float,
        search_interest: float,
        price_ratio: float,
        distance_to_center: float,
        capacity: int,
        rating: float,
    ) -> np.ndarray:
        """Build extended feature vector for booking probability model."""
        season_factor = SEASONALITY_FACTORS.get(target_date.month, 1.0)
        weekday_factor = WEEKDAY_FACTORS.get(target_date.weekday(), 1.0)
        is_weekend = 1.0 if target_date.weekday() >= 4 else 0.0

        return np.array([
            season_factor,
            weekday_factor,
            is_weekend,
            float(days_to_checkin),
            event_impact,
            temperature_forecast,
            rain_probability,
            snow_depth,
            ski_condition_index,
            outdoor_condition_index,
            1.0 if sun_after_snow else 0.0,
            market_occupancy,
            demand_momentum,
            search_interest,
            price_ratio,
            distance_to_center,
            float(capacity),
            rating,
        ])
