"""Tests for WeatherFeatureService – ski index, outdoor index, sun-after-snow."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

from services.weather_feature_service import WeatherFeatureService


class TestWeatherFeatureService:
    def setup_method(self):
        self.forecast_repo = MagicMock()
        self.service = WeatherFeatureService(self.forecast_repo)

    def _make_forecast(self, **overrides):
        defaults = {
            "temperature_forecast": -2.0,
            "temperature_trend": -1.0,
            "snowfall_next_3_days": 10.0,
            "snowfall_next_7_days": 20.0,
            "sun_hours_forecast": 6.0,
            "cloud_cover_forecast": 0.3,
            "rain_probability": 0.1,
            "wind_speed": 10.0,
            "snow_depth": 50.0,
            "fresh_snow": 8.0,
        }
        defaults.update(overrides)
        forecast = MagicMock()
        for k, v in defaults.items():
            setattr(forecast, k, v)
        return forecast

    async def test_ski_condition_index_good_conditions(self):
        forecast = self._make_forecast(
            snow_depth=80.0, fresh_snow=15.0, sun_hours_forecast=8.0,
            temperature_forecast=-3.0, wind_speed=5.0,
        )
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        index = await self.service.compute_ski_condition_index(date(2026, 1, 15), "Berchtesgaden")

        assert index > 5.0  # good conditions
        assert index <= 10.0

    async def test_ski_condition_index_no_snow(self):
        forecast = self._make_forecast(snow_depth=0.0, fresh_snow=0.0)
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        index = await self.service.compute_ski_condition_index(date(2026, 1, 15), "Berchtesgaden")

        assert index == 0.0

    async def test_ski_condition_index_no_forecast(self):
        self.forecast_repo.get_forecast = AsyncMock(return_value=None)

        index = await self.service.compute_ski_condition_index(date(2026, 1, 15), "Berchtesgaden")

        assert index == 0.0

    async def test_outdoor_condition_index_perfect_summer(self):
        forecast = self._make_forecast(
            temperature_forecast=24.0, sun_hours_forecast=10.0,
            rain_probability=0.05, wind_speed=5.0,
        )
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        index = await self.service.compute_outdoor_condition_index(date(2026, 7, 15), "Berchtesgaden")

        assert index > 6.0

    async def test_outdoor_condition_index_rainy(self):
        forecast = self._make_forecast(
            temperature_forecast=18.0, sun_hours_forecast=2.0,
            rain_probability=0.9, wind_speed=20.0,
        )
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        index = await self.service.compute_outdoor_condition_index(date(2026, 7, 15), "Berchtesgaden")

        assert index < 3.0

    async def test_sun_after_snow_detected(self):
        forecast = self._make_forecast(
            snowfall_next_3_days=12.0, sun_hours_forecast=6.0,
        )
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        result = await self.service.detect_sun_after_snow(date(2026, 1, 15), "Berchtesgaden")

        assert result is True

    async def test_sun_after_snow_not_detected(self):
        forecast = self._make_forecast(
            snowfall_next_3_days=2.0, sun_hours_forecast=1.0,
        )
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        result = await self.service.detect_sun_after_snow(date(2026, 1, 15), "Berchtesgaden")

        assert result is False

    async def test_compute_signals_combined(self):
        forecast = self._make_forecast()
        self.forecast_repo.get_forecast = AsyncMock(return_value=forecast)

        signals = await self.service.compute_signals(date(2026, 1, 15), "Berchtesgaden")

        assert signals.ski_condition_index >= 0.0
        assert signals.outdoor_condition_index >= 0.0
        assert isinstance(signals.sun_after_snow, bool)
        assert 0.0 <= signals.demand_spike_probability <= 1.0
