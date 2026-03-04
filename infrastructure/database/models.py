from datetime import date, datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    JSON,
    ForeignKey,
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
