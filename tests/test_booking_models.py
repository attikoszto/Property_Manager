"""Tests for BookingProbabilityModel and BookingWindowModel."""

import numpy as np
import pytest

from ml.models.booking_probability_model import BookingProbabilityModel
from ml.models.booking_window_model import BookingWindowModel


class TestBookingProbabilityModel:
    def _make_training_data(self, n=200):
        rng = np.random.RandomState(42)
        features = rng.rand(n, len(BookingProbabilityModel.FEATURE_NAMES))
        # bias label towards 1 when first feature (season_factor) is high
        labels = (features[:, 0] + rng.rand(n) * 0.4 > 0.7).astype(int)
        return features, labels

    def test_train_xgboost(self):
        model = BookingProbabilityModel(model_type="xgboost")
        X, y = self._make_training_data()
        result = model.train(X, y)

        assert "accuracy" in result
        assert result["n_samples"] == 200
        assert 0.0 <= result["accuracy"] <= 1.0

    def test_train_lightgbm(self):
        model = BookingProbabilityModel(model_type="lightgbm")
        X, y = self._make_training_data()
        result = model.train(X, y)

        assert result["accuracy"] > 0.5

    def test_predict_probability_range(self):
        model = BookingProbabilityModel(model_type="xgboost")
        X, y = self._make_training_data()
        model.train(X, y)

        proba = model.predict_probability(X[:10])
        assert proba.shape == (10,)
        assert np.all(proba >= 0.0) and np.all(proba <= 1.0)

    def test_predict_binary(self):
        model = BookingProbabilityModel(model_type="xgboost")
        X, y = self._make_training_data()
        model.train(X, y)

        preds = model.predict(X[:10])
        assert preds.shape == (10,)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_predict_untrained_raises(self):
        model = BookingProbabilityModel()
        X = np.random.rand(5, len(BookingProbabilityModel.FEATURE_NAMES))
        with pytest.raises(RuntimeError, match="not been trained"):
            model.predict_probability(X)

    def test_feature_importance(self):
        model = BookingProbabilityModel(model_type="xgboost")
        X, y = self._make_training_data()
        model.train(X, y)

        importance = model.get_feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) == len(BookingProbabilityModel.FEATURE_NAMES)
        for name in BookingProbabilityModel.FEATURE_NAMES:
            assert name in importance

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "model.pkl")
        model = BookingProbabilityModel(model_type="xgboost", model_path=path)
        X, y = self._make_training_data()
        model.train(X, y)

        original_proba = model.predict_probability(X[:5])
        model.save()

        loaded = BookingProbabilityModel(model_path=path)
        loaded.load()
        loaded_proba = loaded.predict_probability(X[:5])

        np.testing.assert_array_almost_equal(original_proba, loaded_proba)


class TestBookingWindowModel:
    def _make_training_data(self, n=200):
        rng = np.random.RandomState(42)
        features = rng.rand(n, len(BookingWindowModel.FEATURE_NAMES))
        # lead time ~ 7 to 90 days, correlated with features
        lead_times = 7 + features[:, 0] * 60 + rng.rand(n) * 20
        return features, lead_times

    def test_train(self):
        model = BookingWindowModel()
        X, y = self._make_training_data()
        result = model.train(X, y)

        assert "r2_score" in result
        assert result["n_samples"] == 200
        assert result["mean_lead_time"] > 0

    def test_predict_non_negative(self):
        model = BookingWindowModel()
        X, y = self._make_training_data()
        model.train(X, y)

        preds = model.predict(X[:10])
        assert preds.shape == (10,)
        assert np.all(preds >= 0.0)

    def test_predict_untrained_raises(self):
        model = BookingWindowModel()
        X = np.random.rand(5, len(BookingWindowModel.FEATURE_NAMES))
        with pytest.raises(RuntimeError, match="not been trained"):
            model.predict(X)

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "window_model.pkl")
        model = BookingWindowModel(model_path=path)
        X, y = self._make_training_data()
        model.train(X, y)

        original_preds = model.predict(X[:5])
        model.save()

        loaded = BookingWindowModel(model_path=path)
        loaded.load()
        loaded_preds = loaded.predict(X[:5])

        np.testing.assert_array_almost_equal(original_preds, loaded_preds)
