"""
Booking Probability Model – Predicts the likelihood of a booking for a given date/listing.

Uses XGBoost or LightGBM with advanced demand features including weather forecasts,
ski/outdoor indices, demand momentum, and market signals.
"""

import numpy as np
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import pickle
from pathlib import Path


class BookingProbabilityModel:
    """Predict booking probability given listing + market features.

    Input features:
        weather_forecast, season, events, snow_index, outdoor_index,
        micro_location_score, days_to_checkin, market_occupancy,
        search_interest, demand_momentum, price_ratio

    Output:
        booking_probability (0.0 - 1.0)
    """

    FEATURE_NAMES = [
        "season_factor",
        "weekday_factor",
        "is_weekend",
        "days_to_checkin",
        "event_impact",
        "temperature_forecast",
        "rain_probability",
        "snow_depth",
        "ski_condition_index",
        "outdoor_condition_index",
        "sun_after_snow",
        "market_occupancy",
        "demand_momentum",
        "search_interest",
        "price_ratio",
        "distance_to_center",
        "capacity",
        "rating",
    ]

    def __init__(
        self,
        model_type: str = "xgboost",
        model_path: str = "models/booking_probability.pkl",
    ):
        self.model_path = Path(model_path)
        self.model_type = model_type

        if model_type == "lightgbm":
            self.model = LGBMClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                objective="binary",
                verbose=-1,
            )
        else:
            self.model = XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                objective="binary:logistic",
                eval_metric="logloss",
                use_label_encoder=False,
            )
        self._is_trained = False

    def train(self, features: np.ndarray, labels: np.ndarray) -> dict:
        """Train the model. Labels: 1 = booked, 0 = not booked."""
        self.model.fit(features, labels)
        self._is_trained = True
        score = self.model.score(features, labels)
        return {
            "accuracy": score,
            "n_samples": len(labels),
            "positive_rate": float(labels.mean()),
        }

    def predict_probability(self, features: np.ndarray) -> np.ndarray:
        """Return booking probability for each row."""
        if not self._is_trained:
            raise RuntimeError("Model has not been trained")
        proba = self.model.predict_proba(features)
        return proba[:, 1]  # probability of class 1 (booked)

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Return binary booking predictions."""
        if not self._is_trained:
            raise RuntimeError("Model has not been trained")
        return self.model.predict(features)

    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importance scores."""
        if not self._is_trained:
            raise RuntimeError("Model has not been trained")
        importances = self.model.feature_importances_
        return {
            name: round(float(imp), 4)
            for name, imp in zip(self.FEATURE_NAMES, importances)
            if len(self.FEATURE_NAMES) > 0
        }

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump({"model": self.model, "type": self.model_type}, f)

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"No model found at {self.model_path}")
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.model_type = data["type"]
        self._is_trained = True
