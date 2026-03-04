from infrastructure.database.repository import BookingRepository


class BookingService:
    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    async def record_booking(
        self,
        listing_id: int,
        checkin_date: str,
        checkout_date: str,
        price: float,
        channel: str,
    ) -> int:
        return await self.booking_repo.create(
            listing_id=listing_id,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            price=price,
            channel=channel,
        )

    async def get_bookings_for_listing(self, listing_id: int) -> list:
        return await self.booking_repo.get_by_listing(listing_id)

    async def get_occupancy_rate(self, listing_id: int, start_date: str, end_date: str) -> float:
        return await self.booking_repo.calculate_occupancy(listing_id, start_date, end_date)
