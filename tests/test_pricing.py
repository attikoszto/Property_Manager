from datetime import date
from unittest.mock import AsyncMock, MagicMock

from services.pricing_service import PricingService


class TestPricingService:
    def setup_method(self):
        self.listing_repo = MagicMock()
        self.competitor_repo = MagicMock()
        self.service = PricingService(self.listing_repo, self.competitor_repo)

    async def test_compute_quality_score(self):
        listing = MagicMock()
        listing.rating = 4.8
        listing.review_count = 100
        listing.amenities = ["wifi", "parking", "kitchen"]
        listing.square_meters = 65.0
        self.listing_repo.get_by_id = AsyncMock(return_value=listing)

        score = await self.service.compute_quality_score(1)

        assert score > 0
        assert isinstance(score, float)

    async def test_competition_adjustment_no_competitors(self):
        listing = MagicMock()
        listing.base_price = 100.0
        self.listing_repo.get_by_id = AsyncMock(return_value=listing)
        self.competitor_repo.get_latest_prices = AsyncMock(return_value=[])

        adjustment = await self.service.compute_competition_adjustment(1, [])

        assert adjustment == 1.0

    async def test_competition_adjustment_with_competitors(self):
        listing = MagicMock()
        listing.base_price = 100.0
        self.listing_repo.get_by_id = AsyncMock(return_value=listing)
        self.competitor_repo.get_latest_prices = AsyncMock(return_value=[90, 100, 110])

        adjustment = await self.service.compute_competition_adjustment(1, [2, 3, 4])

        assert adjustment == 1.0  # median of [90, 100, 110] = 100, 100/100 = 1.0

    async def test_competition_adjustment_with_weighted_customers(self):
        listing = MagicMock()
        listing.base_price = 100.0
        self.listing_repo.get_by_id = AsyncMock(return_value=listing)
        # External prices at full weight, customer prices at 0.3 weight
        self.competitor_repo.get_latest_prices = AsyncMock(
            side_effect=[
                [90, 110],   # external competitors
                [150],       # customer listing (high price, low weight)
            ]
        )

        adjustment = await self.service.compute_competition_adjustment(
            1, [2, 3], customer_listing_ids=[4]
        )

        # Weighted median of (90 w=1.0, 110 w=1.0, 150 w=0.3)
        # Total weight = 2.3, half = 1.15
        # Sorted: (90, 1.0) -> cumul 1.0, (110, 1.0) -> cumul 2.0 >= 1.15 → median = 110
        assert adjustment == 1.1  # 110 / 100

    async def test_calculate_price(self):
        listing = MagicMock()
        listing.base_price = 100.0
        listing.rating = 4.5
        listing.review_count = 50
        listing.amenities = ["wifi", "parking"]
        listing.square_meters = 50.0
        self.listing_repo.get_by_id = AsyncMock(return_value=listing)
        self.competitor_repo.get_latest_prices = AsyncMock(return_value=[90, 100, 110])

        price = await self.service.calculate_price(
            listing_id=1,
            demand_index=1.2,
            similar_listing_ids=[2, 3, 4],
        )

        assert price > 0
        assert isinstance(price, float)

    def test_checkin_adjustment_far_out(self):
        future_date = date.today().replace(year=date.today().year + 1)
        adjustment = PricingService.compute_checkin_adjustment(future_date)
        assert adjustment == 1.15

    def test_checkin_adjustment_last_minute(self):
        tomorrow = date.fromordinal(date.today().toordinal() + 1)
        adjustment = PricingService.compute_checkin_adjustment(tomorrow)
        assert adjustment == 0.85

    def test_weighted_median_basic(self):
        result = PricingService._weighted_median([100, 200, 300], [1.0, 1.0, 1.0])
        assert result == 200

    def test_weighted_median_skewed(self):
        # Heavy weight on first value
        result = PricingService._weighted_median([100, 200], [3.0, 1.0])
        assert result == 100

    def test_weighted_median_empty(self):
        result = PricingService._weighted_median([], [])
        assert result == 0.0
