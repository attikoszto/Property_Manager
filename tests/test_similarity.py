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

        assert len(features) == 14  # 7 numeric + 7 amenity features
        assert features[0] == 4  # capacity
        assert features[7] == 1.0  # wifi

    def test_similarity_model_fit_and_find(self):
        model = SimilarityModel(n_neighbors=3)

        features = np.array([
            [4, 2, 1, 65, 4.8, 100, 0.5, 1, 1, 0, 0, 0, 1, 0],
            [2, 1, 1, 40, 4.5, 50, 0.8, 1, 0, 0, 0, 0, 1, 1],
            [6, 3, 2, 120, 4.9, 200, 0.3, 1, 1, 1, 0, 1, 1, 1],
            [4, 2, 1, 60, 4.6, 80, 0.6, 1, 1, 0, 0, 0, 1, 0],
        ])
        listing_ids = [1, 2, 3, 4]

        model.fit(features, listing_ids)
        similar = model.find_similar(features[0], exclude_id=1)

        assert 1 not in similar
        assert len(similar) <= 3

    def test_similarity_model_empty(self):
        model = SimilarityModel(n_neighbors=5)
        features = np.array([[1, 1, 1, 30, 4.0, 10, 1.0, 0, 0, 0, 0, 0, 0, 0]])
        listing_ids = [1]

        model.fit(features, listing_ids)
        similar = model.find_similar(features[0], exclude_id=1)

        assert similar == []


class TestSimilarityServiceFiltering:
    """Test that competitive set filtering excludes customers and same-owner listings."""

    def test_exclude_customers_flag(self):
        """Verify the repository is called with exclude_customers=True by default."""
        from unittest.mock import AsyncMock, MagicMock

        from services.similarity_service import SimilarityService

        listing_repo = MagicMock()

        # Create fake listings with is_customer and owner_id
        def make_listing(id, is_customer=False, owner_id="owner_a"):
            l = MagicMock()
            l.id = id
            l.lat = 47.6310
            l.lng = 13.0020
            l.capacity = 4
            l.bedrooms = 2
            l.bathrooms = 1
            l.square_meters = 65.0
            l.rating = 4.8
            l.review_count = 100
            l.amenities = ["wifi"]
            l.is_customer = is_customer
            l.owner_id = owner_id
            return l

        # External-only listings (customer excluded, owner_b excluded)
        external_listings = [
            make_listing(1, is_customer=False, owner_id="owner_a"),
            make_listing(2, is_customer=False, owner_id="owner_c"),
            make_listing(3, is_customer=False, owner_id="owner_d"),
        ]

        listing_repo.get_all = AsyncMock(return_value=external_listings)
        service = SimilarityService(listing_repo)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.find_similar(1, exclude_customers=True, exclude_owner_id="owner_b")
        )

        listing_repo.get_all.assert_called_once_with(
            exclude_customers=True,
            exclude_owner_id="owner_b",
        )
        assert 1 not in result
