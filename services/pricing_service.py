from datetime import date
from math import log

from core.constants import (
    DAYS_TO_CHECKIN_ADJUSTMENTS,
    EXTERNAL_LISTING_WEIGHT,
    SYSTEM_LISTING_WEIGHT,
)
from infrastructure.database.repository import CompetitorPriceRepository, ListingRepository


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

    @staticmethod
    def _weighted_median(values: list[float], weights: list[float]) -> float:
        """Compute a weighted median of values."""
        if not values:
            return 0.0
        pairs = sorted(zip(values, weights))
        cumulative = 0.0
        total = sum(weights)
        half = total / 2.0
        for value, weight in pairs:
            cumulative += weight
            if cumulative >= half:
                return value
        return pairs[-1][0]

    async def compute_competition_adjustment(
        self,
        listing_id: int,
        similar_listing_ids: list[int],
        customer_listing_ids: list[int] | None = None,
    ) -> float:
        """Compute competition adjustment using weighted competitor prices.

        Args:
            listing_id: The listing to price.
            similar_listing_ids: External (non-customer) competitor listings.
            customer_listing_ids: Optional customer listings included with reduced weight.
        """
        listing = await self.listing_repo.get_by_id(listing_id)

        prices: list[float] = []
        weights: list[float] = []

        # External competitor prices (full weight)
        if similar_listing_ids:
            ext_prices = await self.competitor_repo.get_latest_prices(similar_listing_ids)
            for p in ext_prices:
                prices.append(p)
                weights.append(EXTERNAL_LISTING_WEIGHT)

        # Customer listings at reduced weight (for high market penetration)
        if customer_listing_ids:
            cust_prices = await self.competitor_repo.get_latest_prices(customer_listing_ids)
            for p in cust_prices:
                prices.append(p)
                weights.append(SYSTEM_LISTING_WEIGHT)

        if not prices:
            return 1.0

        median_price = self._weighted_median(prices, weights)
        return median_price / listing.base_price if listing.base_price > 0 else 1.0

    @staticmethod
    def compute_checkin_adjustment(checkin_date: date) -> float:
        days_until = (checkin_date - date.today()).days
        adjustment = 1.0
        for threshold, factor in sorted(DAYS_TO_CHECKIN_ADJUSTMENTS.items(), reverse=True):
            if days_until >= threshold:
                adjustment = factor
                break
        return adjustment

    async def calculate_price(
        self,
        listing_id: int,
        demand_index: float,
        similar_listing_ids: list[int],
        customer_listing_ids: list[int] | None = None,
        checkin_date: date | None = None,
    ) -> float:
        listing = await self.listing_repo.get_by_id(listing_id)
        quality_score = await self.compute_quality_score(listing_id)
        competition_adj = await self.compute_competition_adjustment(
            listing_id, similar_listing_ids, customer_listing_ids
        )

        quality_factor = 1.0 + (quality_score - 5.0) * 0.02
        checkin_adj = self.compute_checkin_adjustment(checkin_date) if checkin_date else 1.0

        return round(
            listing.base_price * demand_index * competition_adj * quality_factor * checkin_adj, 2
        )
