import numpy as np
from datetime import date

from core.constants import SEASONALITY_FACTORS, WEEKDAY_FACTORS


class DemandFeatureBuilder:
    def build(
        self,
        target_date: date,
        event_impact: float,
        weather_temp: float,
        rain_prob: float,
        snow_prob: float,
        occupancy_rate: float,
    ) -> np.ndarray:
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
