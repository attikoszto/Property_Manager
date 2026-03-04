from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class Location:
    lat: float
    lng: float

    def distance_km(self, other: "Location") -> float:
        r = 6371.0
        lat1, lat2 = radians(self.lat), radians(other.lat)
        dlat = radians(other.lat - self.lat)
        dlng = radians(other.lng - self.lng)
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        return r * 2 * asin(sqrt(a))

    def is_within_radius(self, center: "Location", radius_km: float) -> bool:
        return self.distance_km(center) <= radius_km
