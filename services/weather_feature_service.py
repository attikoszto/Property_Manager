"""
Weather Feature Service – Ski Condition Index, Outdoor Index, Sun-After-Snow Signal.

Computes advanced weather-based demand signals for pricing decisions.
"""

from dataclasses import dataclass
from datetime import date

from infrastructure.database.repository import WeatherForecastRepository


@dataclass
class WeatherDemandSignals:
    """Aggregated weather-based demand signals for a stay date."""
    ski_condition_index: float
    outdoor_condition_index: float
    sun_after_snow: bool
    demand_spike_probability: float


# Thresholds for sun-after-snow detection
SNOWFALL_48H_THRESHOLD = 5.0   # cm of new snow in 48 hours
SUN_HOURS_THRESHOLD = 4.0      # hours of sunshine forecast


class WeatherFeatureService:
    def __init__(self, forecast_repo: WeatherForecastRepository):
        self.forecast_repo = forecast_repo

    async def compute_ski_condition_index(
        self, stay_date: date, location: str
    ) -> float:
        """Compute ski condition quality score.

        Formula:
            ski_condition_index = snow_depth × fresh_snow_factor
                                × sun_factor × temperature_factor × wind_factor

        Higher values indicate better ski conditions → higher demand.
        """
        forecast = await self.forecast_repo.get_forecast(stay_date, location)
        if not forecast:
            return 0.0

        # Snow depth baseline (0-1 scale, caps at 100 cm)
        snow_depth_score = min(forecast.snow_depth / 100.0, 1.0)

        # Fresh snow bonus (0.5 base + up to 0.5 bonus for fresh snow)
        fresh_snow_factor = 0.5 + min(forecast.fresh_snow / 20.0, 0.5)

        # Sun factor (skiing in sun is more desirable)
        sun_factor = 0.6 + min(forecast.sun_hours_forecast / 10.0, 0.4)

        # Temperature factor (ideal ski temp: -5 to -1°C; penalize warm temps)
        temp = forecast.temperature_forecast
        if temp <= -10:
            temp_factor = 0.7
        elif temp <= -5:
            temp_factor = 0.9
        elif temp <= 0:
            temp_factor = 1.0
        elif temp <= 5:
            temp_factor = 0.8
        else:
            temp_factor = 0.5

        # Wind factor (high wind reduces ski quality)
        wind_factor = max(0.3, 1.0 - forecast.wind_speed / 60.0)

        index = snow_depth_score * fresh_snow_factor * sun_factor * temp_factor * wind_factor

        # Scale to 0-10 range
        return round(min(index * 10.0, 10.0), 2)

    async def compute_outdoor_condition_index(
        self, stay_date: date, location: str
    ) -> float:
        """Compute summer outdoor activity condition score.

        Formula:
            outdoor_index = temperature_comfort × sun_hours
                          × inverse_rain_probability × wind_factor

        Higher values indicate better outdoor conditions → higher demand.
        """
        forecast = await self.forecast_repo.get_forecast(stay_date, location)
        if not forecast:
            return 0.0

        # Temperature comfort (ideal: 20-25°C)
        temp = forecast.temperature_forecast
        if temp < 10:
            comfort = 0.3
        elif temp < 15:
            comfort = 0.6
        elif temp < 20:
            comfort = 0.8
        elif temp <= 28:
            comfort = 1.0
        elif temp <= 33:
            comfort = 0.8
        else:
            comfort = 0.5

        # Sun hours (0-1 scale, caps at 12 hours)
        sun_score = min(forecast.sun_hours_forecast / 12.0, 1.0)

        # Inverse rain probability
        dry_score = 1.0 - forecast.rain_probability

        # Wind factor
        wind_factor = max(0.3, 1.0 - forecast.wind_speed / 50.0)

        index = comfort * sun_score * dry_score * wind_factor

        return round(min(index * 10.0, 10.0), 2)

    async def detect_sun_after_snow(
        self, stay_date: date, location: str
    ) -> bool:
        """Detect sun-after-snow trigger: new snow followed by sunshine.

        Returns True if:
          - snowfall_last_48h > SNOWFALL_48H_THRESHOLD
          - sun_hours_next_24h > SUN_HOURS_THRESHOLD
        """
        forecast = await self.forecast_repo.get_forecast(stay_date, location)
        if not forecast:
            return False

        # Use snowfall_next_3_days as a proxy for recent + upcoming snow
        recent_snow = forecast.snowfall_next_3_days
        sun_hours = forecast.sun_hours_forecast

        return recent_snow > SNOWFALL_48H_THRESHOLD and sun_hours > SUN_HOURS_THRESHOLD

    async def compute_signals(
        self, stay_date: date, location: str
    ) -> WeatherDemandSignals:
        """Compute all weather-based demand signals for a stay date."""
        ski_index = await self.compute_ski_condition_index(stay_date, location)
        outdoor_index = await self.compute_outdoor_condition_index(stay_date, location)
        sun_snow = await self.detect_sun_after_snow(stay_date, location)

        # Estimate demand spike probability based on signals
        spike_prob = 0.0
        if sun_snow:
            spike_prob += 0.3
        if ski_index > 7.0:
            spike_prob += 0.2
        if outdoor_index > 7.0:
            spike_prob += 0.2
        spike_prob = min(spike_prob, 1.0)

        return WeatherDemandSignals(
            ski_condition_index=ski_index,
            outdoor_condition_index=outdoor_index,
            sun_after_snow=sun_snow,
            demand_spike_probability=spike_prob,
        )
