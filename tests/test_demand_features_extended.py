"""Tests for DemandFeatureBuilder.build_extended() method."""

from datetime import date

import numpy as np

from ml.feature_engineering.demand_features import DemandFeatureBuilder
from ml.models.booking_probability_model import BookingProbabilityModel


class TestDemandFeatureBuilderExtended:
    def setup_method(self):
        self.builder = DemandFeatureBuilder()

    def test_extended_vector_length(self):
        vec = self.builder.build_extended(
            target_date=date(2026, 1, 15),
            days_to_checkin=30,
            event_impact=0.5,
            temperature_forecast=-2.0,
            rain_probability=0.1,
            snow_depth=45.0,
            ski_condition_index=8.5,
            outdoor_condition_index=3.0,
            sun_after_snow=True,
            market_occupancy=0.7,
            demand_momentum=0.05,
            search_interest=65.0,
            price_ratio=1.1,
            distance_to_center=2.5,
            capacity=6,
            rating=4.8,
        )
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (len(BookingProbabilityModel.FEATURE_NAMES),)

    def test_extended_sun_after_snow_encoding(self):
        vec_true = self.builder.build_extended(
            target_date=date(2026, 1, 15),
            days_to_checkin=10,
            event_impact=0.0,
            temperature_forecast=-3.0,
            rain_probability=0.0,
            snow_depth=30.0,
            ski_condition_index=7.0,
            outdoor_condition_index=2.0,
            sun_after_snow=True,
            market_occupancy=0.5,
            demand_momentum=0.0,
            search_interest=50.0,
            price_ratio=1.0,
            distance_to_center=1.0,
            capacity=4,
            rating=4.5,
        )
        vec_false = self.builder.build_extended(
            target_date=date(2026, 1, 15),
            days_to_checkin=10,
            event_impact=0.0,
            temperature_forecast=-3.0,
            rain_probability=0.0,
            snow_depth=30.0,
            ski_condition_index=7.0,
            outdoor_condition_index=2.0,
            sun_after_snow=False,
            market_occupancy=0.5,
            demand_momentum=0.0,
            search_interest=50.0,
            price_ratio=1.0,
            distance_to_center=1.0,
            capacity=4,
            rating=4.5,
        )
        # sun_after_snow is index 10 in FEATURE_NAMES
        assert vec_true[10] == 1.0
        assert vec_false[10] == 0.0

    def test_extended_weekend_detection(self):
        # 2026-01-17 is a Saturday
        vec = self.builder.build_extended(
            target_date=date(2026, 1, 17),
            days_to_checkin=14,
            event_impact=0.0,
            temperature_forecast=0.0,
            rain_probability=0.0,
            snow_depth=0.0,
            ski_condition_index=0.0,
            outdoor_condition_index=0.0,
            sun_after_snow=False,
            market_occupancy=0.5,
            demand_momentum=0.0,
            search_interest=0.0,
            price_ratio=1.0,
            distance_to_center=0.0,
            capacity=2,
            rating=4.0,
        )
        assert vec[2] == 1.0  # is_weekend index

    def test_extended_weekday_detection(self):
        # 2026-01-13 is a Tuesday
        vec = self.builder.build_extended(
            target_date=date(2026, 1, 13),
            days_to_checkin=14,
            event_impact=0.0,
            temperature_forecast=0.0,
            rain_probability=0.0,
            snow_depth=0.0,
            ski_condition_index=0.0,
            outdoor_condition_index=0.0,
            sun_after_snow=False,
            market_occupancy=0.5,
            demand_momentum=0.0,
            search_interest=0.0,
            price_ratio=1.0,
            distance_to_center=0.0,
            capacity=2,
            rating=4.0,
        )
        assert vec[2] == 0.0  # is_weekend index

    def test_basic_build_backward_compatible(self):
        vec = self.builder.build(
            target_date=date(2026, 7, 15),
            event_impact=0.3,
            weather_temp=25.0,
            rain_prob=0.2,
            snow_prob=0.0,
            occupancy_rate=0.65,
        )
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (9,)
