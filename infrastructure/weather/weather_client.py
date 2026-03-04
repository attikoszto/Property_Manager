from dataclasses import dataclass
from datetime import date

import httpx

from core.logging import logger


@dataclass
class WeatherData:
    date: date
    location: str
    temperature: float
    rain_probability: float
    snow_probability: float
    wind_speed: float


@dataclass
class ExtendedWeatherForecast:
    """Rich weather features for a specific stay date."""
    stay_date: date
    location: str
    temperature_forecast: float = 0.0
    temperature_trend: float = 0.0
    snowfall_next_3_days: float = 0.0
    snowfall_next_7_days: float = 0.0
    sun_hours_forecast: float = 0.0
    cloud_cover_forecast: float = 0.0
    rain_probability: float = 0.0
    wind_speed: float = 0.0
    snow_depth: float = 0.0
    fresh_snow: float = 0.0


class WeatherClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    async def get_forecast(self, lat: float, lng: float, days: int = 7) -> list[WeatherData]:
        logger.info("Fetching weather forecast for (%.4f, %.4f)", lat, lng)

        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": "temperature_2m_max,precipitation_probability_max,snowfall_sum,wind_speed_10m_max",
            "forecast_days": days,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temps = daily.get("temperature_2m_max", [])
        rain = daily.get("precipitation_probability_max", [])
        snow = daily.get("snowfall_sum", [])
        wind = daily.get("wind_speed_10m_max", [])

        results = []
        for i, d in enumerate(dates):
            results.append(WeatherData(
                date=date.fromisoformat(d),
                location=f"{lat},{lng}",
                temperature=temps[i] if i < len(temps) else 0.0,
                rain_probability=(rain[i] / 100.0) if i < len(rain) else 0.0,
                snow_probability=min(1.0, (snow[i] / 10.0)) if i < len(snow) else 0.0,
                wind_speed=wind[i] if i < len(wind) else 0.0,
            ))

        return results

    async def get_extended_forecast(
        self, lat: float, lng: float, days: int = 14
    ) -> list[ExtendedWeatherForecast]:
        """Fetch extended forecast with ski/outdoor condition features."""
        logger.info("Fetching extended weather forecast for (%.4f, %.4f)", lat, lng)

        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,snowfall_sum,"
                "wind_speed_10m_max,sunshine_duration,"
                "cloud_cover_mean,snow_depth"
            ),
            "forecast_days": days,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        rain = daily.get("precipitation_probability_max", [])
        snowfall = daily.get("snowfall_sum", [])
        wind = daily.get("wind_speed_10m_max", [])
        sunshine = daily.get("sunshine_duration", [])
        cloud = daily.get("cloud_cover_mean", [])
        snow_depth = daily.get("snow_depth", [])

        results: list[ExtendedWeatherForecast] = []
        for i, d in enumerate(dates):
            temp = temps_max[i] if i < len(temps_max) else 0.0
            temp_prev = temps_max[i - 1] if i > 0 and i - 1 < len(temps_max) else temp
            sf = snowfall[i] if i < len(snowfall) else 0.0

            # Accumulate snowfall over 3-day and 7-day windows
            sf_3d = sum(snowfall[max(0, i - 2): i + 1]) if snowfall else 0.0
            sf_7d = sum(snowfall[max(0, i - 6): i + 1]) if snowfall else 0.0

            sun_hrs = (sunshine[i] / 3600.0) if i < len(sunshine) else 0.0

            results.append(ExtendedWeatherForecast(
                stay_date=date.fromisoformat(d),
                location=f"{lat},{lng}",
                temperature_forecast=temp,
                temperature_trend=temp - temp_prev,
                snowfall_next_3_days=sf_3d,
                snowfall_next_7_days=sf_7d,
                sun_hours_forecast=sun_hrs,
                cloud_cover_forecast=(cloud[i] / 100.0) if i < len(cloud) else 0.5,
                rain_probability=(rain[i] / 100.0) if i < len(rain) else 0.0,
                wind_speed=wind[i] if i < len(wind) else 0.0,
                snow_depth=snow_depth[i] if i < len(snow_depth) else 0.0,
                fresh_snow=sf,
            ))

        return results
