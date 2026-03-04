import numpy as np

from core.constants import AMENITY_FEATURES
from domain.value_objects.location import Location


class FeatureBuilder:
    def __init__(self, center_lat: float = 47.6301, center_lng: float = 13.0044):
        self.center = Location(lat=center_lat, lng=center_lng)

    def build_listing_features(self, listing) -> np.ndarray:
        property_loc = Location(lat=listing.lat, lng=listing.lng)
        distance = property_loc.distance_km(self.center)

        amenity_set = set(listing.amenities or [])
        amenity_vector = [1.0 if a in amenity_set else 0.0 for a in AMENITY_FEATURES]

        return np.array([
            listing.capacity,
            listing.bedrooms,
            listing.bathrooms,
            listing.square_meters,
            listing.rating,
            listing.review_count,
            distance,
            *amenity_vector,
        ])

    def build_batch_features(self, listings: list) -> np.ndarray:
        return np.array([self.build_listing_features(l) for l in listings])
