from datetime import date
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import (
    ListingModel,
    CompetitorPriceModel,
    WeatherModel,
    EventModel,
    BookingModel,
    CleanerModel,
    PropertyCleanerModel,
    CleaningTaskModel,
)


class ListingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, listing_id: int) -> ListingModel:
        result = await self.session.execute(
            select(ListingModel).where(ListingModel.id == listing_id)
        )
        return result.scalar_one()

    async def get_all(self) -> Sequence[ListingModel]:
        result = await self.session.execute(select(ListingModel))
        return result.scalars().all()

    async def get_by_external_id(self, external_id: str) -> ListingModel | None:
        result = await self.session.execute(
            select(ListingModel).where(ListingModel.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def create(self, listing: ListingModel) -> ListingModel:
        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(listing)
        return listing

    async def upsert(self, listing: ListingModel) -> ListingModel:
        existing = await self.get_by_external_id(listing.external_id)
        if existing:
            for attr in [
                "title", "location", "lat", "lng", "capacity", "bedrooms",
                "bathrooms", "square_meters", "rating", "review_count",
                "amenities", "base_price",
            ]:
                setattr(existing, attr, getattr(listing, attr))
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        return await self.create(listing)


class CompetitorPriceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_prices(self, listing_ids: list[int]) -> list[float]:
        result = await self.session.execute(
            select(CompetitorPriceModel.price)
            .where(CompetitorPriceModel.listing_id.in_(listing_ids))
            .where(CompetitorPriceModel.is_available.is_(True))
            .order_by(CompetitorPriceModel.scraped_at.desc())
            .limit(len(listing_ids))
        )
        return [row[0] for row in result.all()]

    async def get_availability_count(self, listing_ids: list[int], target_date: date) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(CompetitorPriceModel)
            .where(CompetitorPriceModel.listing_id.in_(listing_ids))
            .where(CompetitorPriceModel.date == target_date)
            .where(CompetitorPriceModel.is_available.is_(True))
        )
        return result.scalar() or 0

    async def create(self, price: CompetitorPriceModel) -> CompetitorPriceModel:
        self.session.add(price)
        await self.session.commit()
        await self.session.refresh(price)
        return price


class WeatherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_weather(self, target_date: date, location: str) -> WeatherModel | None:
        result = await self.session.execute(
            select(WeatherModel)
            .where(WeatherModel.date == target_date)
            .where(WeatherModel.location == location)
        )
        return result.scalar_one_or_none()

    async def create(self, weather: WeatherModel) -> WeatherModel:
        self.session.add(weather)
        await self.session.commit()
        await self.session.refresh(weather)
        return weather


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_events_for_date(self, target_date: date, location: str) -> Sequence[EventModel]:
        result = await self.session.execute(
            select(EventModel)
            .where(EventModel.date == target_date)
            .where(EventModel.location == location)
        )
        return result.scalars().all()

    async def create(self, event: EventModel) -> EventModel:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> int:
        booking = BookingModel(**kwargs)
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking.id

    async def get_by_listing(self, listing_id: int) -> Sequence[BookingModel]:
        result = await self.session.execute(
            select(BookingModel).where(BookingModel.listing_id == listing_id)
        )
        return result.scalars().all()

    async def calculate_occupancy(
        self, listing_id: int, start_date: str, end_date: str
    ) -> float:
        result = await self.session.execute(
            select(func.count())
            .select_from(BookingModel)
            .where(BookingModel.listing_id == listing_id)
            .where(BookingModel.checkin_date >= start_date)
            .where(BookingModel.checkout_date <= end_date)
        )
        booking_count = result.scalar() or 0
        from datetime import datetime
        d1 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(end_date, "%Y-%m-%d").date()
        total_days = (d2 - d1).days
        return booking_count / max(total_days, 1)


class CleanerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_property(self, property_id: int) -> Sequence[PropertyCleanerModel]:
        result = await self.session.execute(
            select(PropertyCleanerModel)
            .where(PropertyCleanerModel.property_id == property_id)
            .order_by(PropertyCleanerModel.priority)
        )
        return result.scalars().all()

    async def check_availability(self, cleaner_id: int, check_date: str) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(CleaningTaskModel)
            .where(CleaningTaskModel.assigned_cleaner_id == cleaner_id)
            .where(CleaningTaskModel.check_out_date == check_date)
            .where(CleaningTaskModel.status.in_(["assigned", "in_progress"]))
        )
        count = result.scalar() or 0
        return count == 0

    async def create(self, cleaner: CleanerModel) -> CleanerModel:
        self.session.add(cleaner)
        await self.session.commit()
        await self.session.refresh(cleaner)
        return cleaner


class CleaningTaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, property_id: int, check_out_date: str) -> int:
        task = CleaningTaskModel(property_id=property_id, check_out_date=check_out_date)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task.id

    async def get_by_id(self, task_id: int) -> CleaningTaskModel:
        result = await self.session.execute(
            select(CleaningTaskModel).where(CleaningTaskModel.id == task_id)
        )
        return result.scalar_one()

    async def get_by_property(self, property_id: int) -> Sequence[CleaningTaskModel]:
        result = await self.session.execute(
            select(CleaningTaskModel).where(CleaningTaskModel.property_id == property_id)
        )
        return result.scalars().all()

    async def assign(self, task_id: int, cleaner_id: int) -> None:
        task = await self.get_by_id(task_id)
        task.assigned_cleaner_id = cleaner_id
        task.status = "assigned"
        await self.session.commit()

    async def update_status(self, task_id: int, status: str) -> None:
        task = await self.get_by_id(task_id)
        task.status = status
        await self.session.commit()
