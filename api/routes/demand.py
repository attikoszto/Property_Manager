from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.dependencies import get_demand_service, get_similarity_service
from services.demand_service import DemandService
from services.similarity_service import SimilarityService

router = APIRouter()


class DemandForecast(BaseModel):
    date: date
    location: str
    demand_index: float
    season_factor: float
    weekday_factor: float


@router.get("/forecast", response_model=DemandForecast)
async def get_demand_forecast(
    listing_id: int = Query(...),
    target_date: date = Query(default_factory=date.today),
    demand_service: DemandService = Depends(get_demand_service),
    similarity_service: SimilarityService = Depends(get_similarity_service),
):
    similar_ids = await similarity_service.find_similar(listing_id)
    demand_index = await demand_service.compute_demand_index(
        target_date=target_date,
        location="Berchtesgaden",
        listing_ids=similar_ids,
    )

    return DemandForecast(
        date=target_date,
        location="Berchtesgaden",
        demand_index=demand_index,
        season_factor=demand_service.get_season_factor(target_date),
        weekday_factor=demand_service.get_weekday_factor(target_date),
    )
