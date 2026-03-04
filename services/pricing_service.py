from math import log

from core.constants import SEASONALITY_FACTORS, WEEKDAY_FACTORS
from infrastructure.database.repository import ListingRepository, CompetitorPriceRepository


class PricingService:
    def __init__(
        self,
        listing_repo: ListingRepository,
        competitor_repo: CompetitorPriceRepository,
    ):
        self.listing_repo = listing_repo
        self.competitor_repo = competitor_repo

    async def compute_quality_score(self, listing_id: int) -> float:
        listing = await self.listing_repo.get_by_id(listing_id)
        amenity_count = len(listing.amenities) if listing.amenities else 0
        return (
            listing.rating * 2
            + log(max(listing.review_count, 1))
            + amenity_count * 0.5
            + listing.square_meters * 0.02
        )

    async def compute_competition_adjustment(
        self, listing_id: int, similar_listing_ids: list[int]
    ) -> float:
        listing = await self.listing_repo.get_by_id(listing_id)
        prices = await self.competitor_repo.get_latest_prices(similar_listing_ids)
        if not prices:
            return 1.0
        median_price = sorted(prices)[len(prices) // 2]
        return median_price / listing.base_price if listing.base_price > 0 else 1.0

    async def calculate_price(
        self,
        listing_id: int,
        demand_index: float,
        similar_listing_ids: list[int],
    ) -> float:
        listing = await self.listing_repo.get_by_id(listing_id)
        quality_score = await self.compute_quality_score(listing_id)
        competition_adj = await self.compute_competition_adjustment(
            listing_id, similar_listing_ids
        )

        quality_factor = 1.0 + (quality_score - 5.0) * 0.02

        return round(
            listing.base_price * demand_index * competition_adj * quality_factor, 2
        )
