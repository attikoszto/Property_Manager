import numpy as np

from ml.feature_engineering.feature_builder import FeatureBuilder
from ml.models.similarity_model import SimilarityModel


class TestSimilarity:
    def test_feature_builder(self):
        builder = FeatureBuilder()

        class FakeListing:
            lat = 47.6310
            lng = 13.0020
            capacity = 4
            bedrooms = 2
            bathrooms = 1
            square_meters = 65.0
            rating = 4.8
            review_count = 124
            amenities = ["wifi", "parking", "kitchen"]

        features = builder.build_listing_features(FakeListing())

        assert len(features) == 15  # 7 numeric + 8 amenity features
        assert features[0] == 4  # capacity
        assert features[7] == 1.0  # wifi

    def test_similarity_model_fit_and_find(self):
        model = SimilarityModel(n_neighbors=3)

        features = np.array([
            [4, 2, 1, 65, 4.8, 100, 0.5, 1, 1, 0, 0, 0, 1, 0, 0],
            [2, 1, 1, 40, 4.5, 50, 0.8, 1, 0, 0, 0, 0, 1, 1, 0],
            [6, 3, 2, 120, 4.9, 200, 0.3, 1, 1, 1, 0, 1, 1, 1, 1],
            [4, 2, 1, 60, 4.6, 80, 0.6, 1, 1, 0, 0, 0, 1, 0, 0],
        ])
        listing_ids = [1, 2, 3, 4]

        model.fit(features, listing_ids)
        similar = model.find_similar(features[0], exclude_id=1)

        assert 1 not in similar
        assert len(similar) <= 3

    def test_similarity_model_empty(self):
        model = SimilarityModel(n_neighbors=5)
        features = np.array([[1, 1, 1, 30, 4.0, 10, 1.0, 0, 0, 0, 0, 0, 0, 0, 0]])
        listing_ids = [1]

        model.fit(features, listing_ids)
        similar = model.find_similar(features[0], exclude_id=1)

        assert similar == []
