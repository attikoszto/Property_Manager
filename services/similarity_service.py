import numpy as np
from sklearn.neighbors import NearestNeighbors

from core.constants import AMENITY_FEATURES, SIMILARITY_TOP_K
from domain.value_objects.location import Location
from infrastructure.database.repository import ListingRepository


class SimilarityService:
    def __init__(self, listing_repo: ListingRepository):
        self.listing_repo = listing_repo

    def _build_feature_vector(self, listing) -> list[float]:
        center = Location(lat=47.6301, lng=13.0044)
        property_loc = Location(lat=listing.lat, lng=listing.lng)
        distance_to_center = property_loc.distance_km(center)

        amenity_set = set(listing.amenities or [])
        amenity_vector = [1.0 if a in amenity_set else 0.0 for a in AMENITY_FEATURES]

        return [
            listing.capacity,
            listing.bedrooms,
            listing.bathrooms,
            listing.square_meters,
            listing.rating,
            listing.review_count,
            distance_to_center,
            *amenity_vector,
        ]

    async def find_similar(self, listing_id: int, top_k: int = SIMILARITY_TOP_K) -> list[int]:
        all_listings = await self.listing_repo.get_all()
        if len(all_listings) < 2:
            return []

        target = None
        listing_ids = []
        features = []

        for listing in all_listings:
            if listing.id == listing_id:
                target = listing
            listing_ids.append(listing.id)
            features.append(self._build_feature_vector(listing))

        if target is None:
            return []

        feature_matrix = np.array(features)
        k = min(top_k + 1, len(feature_matrix))

        model = NearestNeighbors(n_neighbors=k, metric="euclidean")
        model.fit(feature_matrix)

        target_idx = listing_ids.index(listing_id)
        target_vector = feature_matrix[target_idx].reshape(1, -1)

        distances, indices = model.kneighbors(target_vector)

        similar_ids = [
            listing_ids[idx]
            for idx in indices[0]
            if listing_ids[idx] != listing_id
        ]

        return similar_ids[:top_k]
