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
