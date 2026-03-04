from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Property Manager"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/property_manager"
    database_sync_url: str = "postgresql://postgres:postgres@localhost:5433/property_manager"

    redis_url: str = "redis://localhost:6379/0"

    region_center_lat: float = 47.6301
    region_center_lng: float = 13.0044
    region_radius_km: float = 5.0

    scraping_interval_hours: int = 24
    model_training_interval_hours: int = 24

    class Config:
        env_file = ".env"
        env_prefix = "PM_"


settings = Settings()
