import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor


class DemandModel:
    def __init__(self, model_path: str = "models/demand_model.pkl"):
        self.model_path = Path(model_path)
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
        )
        self._is_trained = False

    def train(self, features: np.ndarray, targets: np.ndarray) -> dict:
        self.model.fit(features, targets)
        self._is_trained = True
        score = self.model.score(features, targets)
        return {"r2_score": score, "n_samples": len(targets)}

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not self._is_trained:
            raise RuntimeError("Model has not been trained")
        return self.model.predict(features)

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
