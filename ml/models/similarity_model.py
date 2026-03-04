import pickle
from pathlib import Path

import numpy as np
from sklearn.neighbors import NearestNeighbors


class SimilarityModel:
    def __init__(self, n_neighbors: int = 20, model_path: str = "models/similarity_model.pkl"):
        self.n_neighbors = n_neighbors
        self.model_path = Path(model_path)
        self.model = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
        self.listing_ids: list[int] = []
        self._is_fitted = False

    def fit(self, features: np.ndarray, listing_ids: list[int]) -> None:
        self.listing_ids = listing_ids
        k = min(self.n_neighbors, len(features))
        self.model = NearestNeighbors(n_neighbors=k, metric="euclidean")
        self.model.fit(features)
        self._is_fitted = True

    def find_similar(self, feature_vector: np.ndarray, exclude_id: int | None = None) -> list[int]:
        if not self._is_fitted:
            raise RuntimeError("Model has not been fitted")

        distances, indices = self.model.kneighbors(feature_vector.reshape(1, -1))

        results = []
        for idx in indices[0]:
            lid = self.listing_ids[idx]
            if lid != exclude_id:
                results.append(lid)

        return results

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"model": self.model, "listing_ids": self.listing_ids}
        with open(self.model_path, "wb") as f:
            pickle.dump(data, f)

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"No model found at {self.model_path}")
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.listing_ids = data["listing_ids"]
        self._is_fitted = True
