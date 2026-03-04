from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from infrastructure.database.session import Base


class ListingModel(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), unique=True, nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    square_meters = Column(Float, nullable=False)
    rating = Column(Float, nullable=False, default=0.0)
    review_count = Column(Integer, nullable=False, default=0)
    amenities = Column(JSON, nullable=True)
    base_price = Column(Float, nullable=False)
    owner_id = Column(String(255), nullable=True)
    is_customer = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompetitorPriceModel(Base):
    __tablename__ = "competitor_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class WeatherModel(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    location = Column(String(255), nullable=False)
    temperature = Column(Float, nullable=False)
    rain_probability = Column(Float, nullable=False)
    snow_probability = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)


class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(500), nullable=False)
    location = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    impact_score = Column(Float, nullable=False)


class BookingModel(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    checkin_date = Column(Date, nullable=False)
    checkout_date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    booked_at = Column(DateTime, default=datetime.utcnow)
    channel = Column(String(50), nullable=False)


class CleanerModel(Base):
    __tablename__ = "cleaners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    availability_schedule = Column(JSON, nullable=True)


class PropertyCleanerModel(Base):
    __tablename__ = "property_cleaners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    cleaner_id = Column(Integer, ForeignKey("cleaners.id"), nullable=False)
    priority = Column(Integer, default=1)


class AvailabilitySnapshotModel(Base):
    __tablename__ = "availability_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    is_available = Column(Boolean, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class CleaningTaskModel(Base):
    __tablename__ = "cleaning_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    check_out_date = Column(Date, nullable=False)
    assigned_cleaner_id = Column(Integer, ForeignKey("cleaners.id"), nullable=True)
    status = Column(String(50), default="pending")


class WeatherForecastModel(Base):
    """Extended weather forecast features per stay date."""
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stay_date = Column(Date, nullable=False, index=True)
    location = Column(String(255), nullable=False)
    temperature_forecast = Column(Float, nullable=False)
    temperature_trend = Column(Float, nullable=False, default=0.0)
    snowfall_next_3_days = Column(Float, nullable=False, default=0.0)
    snowfall_next_7_days = Column(Float, nullable=False, default=0.0)
    sun_hours_forecast = Column(Float, nullable=False, default=0.0)
    cloud_cover_forecast = Column(Float, nullable=False, default=0.0)
    rain_probability = Column(Float, nullable=False, default=0.0)
    wind_speed = Column(Float, nullable=False, default=0.0)
    snow_depth = Column(Float, nullable=False, default=0.0)
    fresh_snow = Column(Float, nullable=False, default=0.0)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class SearchDemandModel(Base):
    """Google Trends / search interest signals."""
    __tablename__ = "search_demand"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_term = Column(String(500), nullable=False)
    location = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    search_interest_index = Column(Float, nullable=False)
    search_interest_trend = Column(Float, nullable=False, default=0.0)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class FlightPriceModel(Base):
    """Flight price signals for international tourism demand."""
    __tablename__ = "flight_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin = Column(String(10), nullable=False)
    destination = Column(String(10), nullable=False)
    travel_date = Column(Date, nullable=False, index=True)
    average_price = Column(Float, nullable=False)
    price_trend = Column(Float, nullable=False, default=0.0)
    availability_score = Column(Float, nullable=False, default=1.0)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class MarketSnapshotModel(Base):
    """Daily market-level aggregation for saturation and momentum signals."""
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    location = Column(String(255), nullable=False)
    total_listings = Column(Integer, nullable=False)
    available_listings = Column(Integer, nullable=False)
    median_price = Column(Float, nullable=False)
    avg_occupancy_rate = Column(Float, nullable=False)
    booking_velocity = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
