"""
Ingest weather forecast data and store extended features per stay date.

Can be run alongside the scraping pipeline or independently.
"""

import asyncio

from core.constants import BERCHTESGADEN_LAT, BERCHTESGADEN_LNG
from core.logging import logger
from infrastructure.database.session import async_session, engine
from infrastructure.database.models import Base, WeatherForecastModel
from infrastructure.database.repository import WeatherForecastRepository
from infrastructure.weather.weather_client import WeatherClient


async def ingest_weather_forecasts() -> None:
    """Fetch extended weather forecasts and store in weather_forecasts table."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    client = WeatherClient()
    forecasts = await client.get_extended_forecast(
        BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, days=14
    )

    async with async_session() as session:
        repo = WeatherForecastRepository(session)
        count = 0

        for f in forecasts:
            record = WeatherForecastModel(
                stay_date=f.stay_date,
                location=f.location,
                temperature_forecast=f.temperature_forecast,
                temperature_trend=f.temperature_trend,
                snowfall_next_3_days=f.snowfall_next_3_days,
                snowfall_next_7_days=f.snowfall_next_7_days,
                sun_hours_forecast=f.sun_hours_forecast,
                cloud_cover_forecast=f.cloud_cover_forecast,
                rain_probability=f.rain_probability,
                wind_speed=f.wind_speed,
                snow_depth=f.snow_depth,
                fresh_snow=f.fresh_snow,
            )
            await repo.upsert(record)
            count += 1

        logger.info("Ingested %d weather forecasts", count)


if __name__ == "__main__":
    asyncio.run(ingest_weather_forecasts())
