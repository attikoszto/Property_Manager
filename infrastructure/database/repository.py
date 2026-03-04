from collections.abc import Sequence
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import (
    AvailabilitySnapshotModel,
    BookingModel,
    CleanerModel,
    CleaningTaskModel,
    CompetitorPriceModel,
    EventModel,
    FlightPriceModel,
    ListingModel,
    MarketSnapshotModel,
    PropertyCleanerModel,
    SearchDemandModel,
    WeatherForecastModel,
    WeatherModel,
)


class ListingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, listing_id: int) -> ListingModel:
        result = await self.session.execute(
            select(ListingModel).where(ListingModel.id == listing_id)
        )
        return result.scalar_one()

    async def get_all(
        self,
        exclude_customers: bool = False,
        exclude_owner_id: str | None = None,
    ) -> Sequence[ListingModel]:
        query = select(ListingModel)
        if exclude_customers:
            query = query.where(ListingModel.is_customer.is_(False))
        if exclude_owner_id:
            query = query.where(ListingModel.owner_id != exclude_owner_id)
        result = await self.session.execute(query)
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
            # Only update ownership fields if explicitly set
            if listing.owner_id is not None:
                existing.owner_id = listing.owner_id
            if listing.is_customer is not None:
                existing.is_customer = listing.is_customer
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        # For new inserts ensure is_customer defaults
        if listing.is_customer is None:
            listing.is_customer = False
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

    async def get_latest_prices_with_listing(
        self, listing_ids: list[int]
    ) -> list[tuple[int, float]]:
        """Return (listing_id, price) pairs for weighted competitor analysis."""
        result = await self.session.execute(
            select(CompetitorPriceModel.listing_id, CompetitorPriceModel.price)
            .where(CompetitorPriceModel.listing_id.in_(listing_ids))
            .where(CompetitorPriceModel.is_available.is_(True))
            .order_by(CompetitorPriceModel.scraped_at.desc())
            .limit(len(listing_ids))
        )
        return [(row[0], row[1]) for row in result.all()]

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


class AvailabilityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_snapshot(
        self, listing_id: int, snapshot_date: date, is_available: bool
    ) -> AvailabilitySnapshotModel:
        snapshot = AvailabilitySnapshotModel(
            listing_id=listing_id, date=snapshot_date, is_available=is_available
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot

    async def detect_bookings(self, snapshot_date: date) -> list[int]:
        yesterday = date.fromordinal(snapshot_date.toordinal() - 1)
        prev = await self.session.execute(
            select(AvailabilitySnapshotModel.listing_id)
            .where(AvailabilitySnapshotModel.date == yesterday)
            .where(AvailabilitySnapshotModel.is_available.is_(True))
        )
        was_available = {row[0] for row in prev.all()}

        curr = await self.session.execute(
            select(AvailabilitySnapshotModel.listing_id)
            .where(AvailabilitySnapshotModel.date == snapshot_date)
            .where(AvailabilitySnapshotModel.is_available.is_(False))
        )
        now_unavailable = {row[0] for row in curr.all()}

        return list(was_available & now_unavailable)

    async def compute_market_occupancy(self, snapshot_date: date) -> float:
        total = await self.session.execute(
            select(func.count())
            .select_from(AvailabilitySnapshotModel)
            .where(AvailabilitySnapshotModel.date == snapshot_date)
        )
        total_count = total.scalar() or 0

        blocked = await self.session.execute(
            select(func.count())
            .select_from(AvailabilitySnapshotModel)
            .where(AvailabilitySnapshotModel.date == snapshot_date)
            .where(AvailabilitySnapshotModel.is_available.is_(False))
        )
        blocked_count = blocked.scalar() or 0

        return blocked_count / total_count if total_count > 0 else 0.0


class WeatherForecastRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_forecast(self, stay_date: date, location: str) -> WeatherForecastModel | None:
        result = await self.session.execute(
            select(WeatherForecastModel)
            .where(WeatherForecastModel.stay_date == stay_date)
            .where(WeatherForecastModel.location == location)
            .order_by(WeatherForecastModel.fetched_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_range(
        self, start_date: date, end_date: date, location: str
    ) -> Sequence[WeatherForecastModel]:
        result = await self.session.execute(
            select(WeatherForecastModel)
            .where(WeatherForecastModel.stay_date >= start_date)
            .where(WeatherForecastModel.stay_date <= end_date)
            .where(WeatherForecastModel.location == location)
            .order_by(WeatherForecastModel.stay_date)
        )
        return result.scalars().all()

    async def upsert(self, forecast: WeatherForecastModel) -> WeatherForecastModel:
        existing = await self.get_forecast(forecast.stay_date, forecast.location)
        if existing:
            for attr in [
                "temperature_forecast", "temperature_trend",
                "snowfall_next_3_days", "snowfall_next_7_days",
                "sun_hours_forecast", "cloud_cover_forecast",
                "rain_probability", "wind_speed", "snow_depth", "fresh_snow",
            ]:
                setattr(existing, attr, getattr(forecast, attr))
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        self.session.add(forecast)
        await self.session.commit()
        await self.session.refresh(forecast)
        return forecast


class SearchDemandRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, query_term: str, location: str) -> SearchDemandModel | None:
        result = await self.session.execute(
            select(SearchDemandModel)
            .where(SearchDemandModel.query_term == query_term)
            .where(SearchDemandModel.location == location)
            .order_by(SearchDemandModel.date.desc())
        )
        return result.scalars().first()

    async def get_trend(
        self, query_term: str, location: str, days: int = 30
    ) -> Sequence[SearchDemandModel]:
        cutoff = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(SearchDemandModel)
            .where(SearchDemandModel.query_term == query_term)
            .where(SearchDemandModel.location == location)
            .where(SearchDemandModel.date >= cutoff)
            .order_by(SearchDemandModel.date)
        )
        return result.scalars().all()

    async def create(self, record: SearchDemandModel) -> SearchDemandModel:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record


class FlightPriceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(
        self, origin: str, destination: str, travel_date: date
    ) -> FlightPriceModel | None:
        result = await self.session.execute(
            select(FlightPriceModel)
            .where(FlightPriceModel.origin == origin)
            .where(FlightPriceModel.destination == destination)
            .where(FlightPriceModel.travel_date == travel_date)
            .order_by(FlightPriceModel.fetched_at.desc())
        )
        return result.scalars().first()

    async def create(self, record: FlightPriceModel) -> FlightPriceModel:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record


class MarketSnapshotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, location: str) -> MarketSnapshotModel | None:
        result = await self.session.execute(
            select(MarketSnapshotModel)
            .where(MarketSnapshotModel.location == location)
            .order_by(MarketSnapshotModel.date.desc())
        )
        return result.scalars().first()

    async def get_trend(
        self, location: str, days: int = 7
    ) -> Sequence[MarketSnapshotModel]:
        cutoff = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(MarketSnapshotModel)
            .where(MarketSnapshotModel.location == location)
            .where(MarketSnapshotModel.date >= cutoff)
            .order_by(MarketSnapshotModel.date)
        )
        return result.scalars().all()

    async def create(self, snapshot: MarketSnapshotModel) -> MarketSnapshotModel:
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot
