"""
Booking Window Model – Predicts expected booking lead time (days before check-in).

Features: season, property_type, location, price, day_of_week, holiday_calendar.
Output: expected_booking_lead_time (days).
"""

import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor


class BookingWindowModel:
    """Predict how many days before check-in a booking is likely to occur.

    This allows better price adjustments based on booking window behavior.
    Short predicted lead times → more aggressive last-minute pricing.
    Long predicted lead times → earlier price optimization opportunities.
    """

    FEATURE_NAMES = [
        "season_factor",
        "month",
        "day_of_week",
        "is_weekend_checkin",
        "is_holiday",
        "capacity",
        "bedrooms",
        "rating",
        "base_price",
        "distance_to_center",
        "market_occupancy",
    ]

    def __init__(self, model_path: str = "models/booking_window.pkl"):
        self.model_path = Path(model_path)
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
        )
        self._is_trained = False

    def train(self, features: np.ndarray, lead_times: np.ndarray) -> dict:
        """Train on historical booking data. Targets: days between booking and check-in."""
        self.model.fit(features, lead_times)
        self._is_trained = True
        score = self.model.score(features, lead_times)
        return {
            "r2_score": score,
            "n_samples": len(lead_times),
            "mean_lead_time": float(lead_times.mean()),
        }

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Return expected lead time in days."""
        if not self._is_trained:
            raise RuntimeError("Model has not been trained")
        predictions = self.model.predict(features)
        return np.maximum(predictions, 0.0)  # lead time can't be negative

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"No model found at {self.model_path}")
        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)
        self._is_trained = True
