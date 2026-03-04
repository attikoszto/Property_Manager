from fastapi import FastAPI

from api.routes import listings, pricing, cleaners, demand, signals
from app.lifespan import lifespan

app = FastAPI(
    title="AI Property Manager",
    description="AI-driven revenue optimization for short-term rentals",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(listings.router, prefix="/listings", tags=["listings"])
app.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
app.include_router(cleaners.router, prefix="/cleaners", tags=["cleaners"])
app.include_router(demand.router, prefix="/demand", tags=["demand"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
