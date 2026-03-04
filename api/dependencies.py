from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.repository import (
    AvailabilityRepository,
    BookingRepository,
    CleanerRepository,
    CleaningTaskRepository,
    CompetitorPriceRepository,
    EventRepository,
    FlightPriceRepository,
    ListingRepository,
    MarketSnapshotRepository,
    SearchDemandRepository,
    WeatherForecastRepository,
    WeatherRepository,
)
from infrastructure.database.session import get_session
from services.booking_service import BookingService
from services.cleaning_service import CleaningService
from services.demand_service import DemandService
from services.market_analysis_service import MarketAnalysisService
from services.pricing_service import PricingService
from services.similarity_service import SimilarityService
from services.weather_feature_service import WeatherFeatureService


async def get_listing_repo(session: AsyncSession = Depends(get_session)) -> ListingRepository:
    return ListingRepository(session)


async def get_competitor_repo(session: AsyncSession = Depends(get_session)) -> CompetitorPriceRepository:
    return CompetitorPriceRepository(session)


async def get_event_repo(session: AsyncSession = Depends(get_session)) -> EventRepository:
    return EventRepository(session)


async def get_weather_repo(session: AsyncSession = Depends(get_session)) -> WeatherRepository:
    return WeatherRepository(session)


async def get_cleaner_repo(session: AsyncSession = Depends(get_session)) -> CleanerRepository:
    return CleanerRepository(session)


async def get_task_repo(session: AsyncSession = Depends(get_session)) -> CleaningTaskRepository:
    return CleaningTaskRepository(session)


async def get_booking_repo(session: AsyncSession = Depends(get_session)) -> BookingRepository:
    return BookingRepository(session)


async def get_availability_repo(session: AsyncSession = Depends(get_session)) -> AvailabilityRepository:
    return AvailabilityRepository(session)


async def get_weather_forecast_repo(session: AsyncSession = Depends(get_session)) -> WeatherForecastRepository:
    return WeatherForecastRepository(session)


async def get_search_demand_repo(session: AsyncSession = Depends(get_session)) -> SearchDemandRepository:
    return SearchDemandRepository(session)


async def get_flight_price_repo(session: AsyncSession = Depends(get_session)) -> FlightPriceRepository:
    return FlightPriceRepository(session)


async def get_market_snapshot_repo(session: AsyncSession = Depends(get_session)) -> MarketSnapshotRepository:
    return MarketSnapshotRepository(session)


async def get_pricing_service(
    listing_repo: ListingRepository = Depends(get_listing_repo),
    competitor_repo: CompetitorPriceRepository = Depends(get_competitor_repo),
) -> PricingService:
    return PricingService(listing_repo, competitor_repo)


async def get_demand_service(
    event_repo: EventRepository = Depends(get_event_repo),
    weather_repo: WeatherRepository = Depends(get_weather_repo),
    competitor_repo: CompetitorPriceRepository = Depends(get_competitor_repo),
    availability_repo: AvailabilityRepository = Depends(get_availability_repo),
) -> DemandService:
    return DemandService(event_repo, weather_repo, competitor_repo, availability_repo)


async def get_similarity_service(
    listing_repo: ListingRepository = Depends(get_listing_repo),
) -> SimilarityService:
    return SimilarityService(listing_repo)


async def get_cleaning_service(
    cleaner_repo: CleanerRepository = Depends(get_cleaner_repo),
    task_repo: CleaningTaskRepository = Depends(get_task_repo),
) -> CleaningService:
    return CleaningService(cleaner_repo, task_repo)


async def get_booking_service(
    booking_repo: BookingRepository = Depends(get_booking_repo),
) -> BookingService:
    return BookingService(booking_repo)


async def get_weather_feature_service(
    forecast_repo: WeatherForecastRepository = Depends(get_weather_forecast_repo),
) -> WeatherFeatureService:
    return WeatherFeatureService(forecast_repo)


async def get_market_analysis_service(
    market_repo: MarketSnapshotRepository = Depends(get_market_snapshot_repo),
    availability_repo: AvailabilityRepository = Depends(get_availability_repo),
    competitor_repo: CompetitorPriceRepository = Depends(get_competitor_repo),
    search_repo: SearchDemandRepository = Depends(get_search_demand_repo),
    flight_repo: FlightPriceRepository = Depends(get_flight_price_repo),
) -> MarketAnalysisService:
    return MarketAnalysisService(
        market_repo, availability_repo, competitor_repo, search_repo, flight_repo
    )
