"""
Bootstrap the initial Berchtesgaden region.

Defines center coordinates, calculates bounding box,
and prepares for initial data collection within 5 km radius.
"""

import asyncio
from geopy.distance import geodesic

from core.constants import BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM
from core.logging import logger


def calculate_bounding_box(
    center_lat: float, center_lng: float, radius_km: float
) -> dict:
    north = geodesic(kilometers=radius_km).destination((center_lat, center_lng), bearing=0)
    south = geodesic(kilometers=radius_km).destination((center_lat, center_lng), bearing=180)
    east = geodesic(kilometers=radius_km).destination((center_lat, center_lng), bearing=90)
    west = geodesic(kilometers=radius_km).destination((center_lat, center_lng), bearing=270)

    return {
        "north": north.latitude,
        "south": south.latitude,
        "east": east.longitude,
        "west": west.longitude,
    }


async def bootstrap() -> None:
    logger.info("Bootstrapping Berchtesgaden region")
    logger.info("Center: (%.4f, %.4f)", BERCHTESGADEN_LAT, BERCHTESGADEN_LNG)
    logger.info("Radius: %.1f km", DEFAULT_RADIUS_KM)

    bbox = calculate_bounding_box(BERCHTESGADEN_LAT, BERCHTESGADEN_LNG, DEFAULT_RADIUS_KM)
    logger.info("Bounding box: %s", bbox)

    logger.info("Region bootstrap complete")


if __name__ == "__main__":
    asyncio.run(bootstrap())
