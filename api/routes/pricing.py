from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.dependencies import get_pricing_service, get_demand_service, get_similarity_service
from services.pricing_service import PricingService
from services.demand_service import DemandService
from services.similarity_service import SimilarityService

router = APIRouter()


class PriceRecommendation(BaseModel):
    listing_id: int
    date: date
    demand_index: float
    recommended_price: float
    quality_score: float
    competition_adjustment: float


@router.get("/recommendation", response_model=PriceRecommendation)
async def get_price_recommendation(
    listing_id: int = Query(...),
    target_date: date = Query(default_factory=date.today),
    pricing_service: PricingService = Depends(get_pricing_service),
    demand_service: DemandService = Depends(get_demand_service),
    similarity_service: SimilarityService = Depends(get_similarity_service),
):
    similar_ids = await similarity_service.find_similar(listing_id)
    demand_index = await demand_service.compute_demand_index(
        target_date=target_date,
        location="Berchtesgaden",
        listing_ids=similar_ids,
    )
    quality_score = await pricing_service.compute_quality_score(listing_id)
    competition_adj = await pricing_service.compute_competition_adjustment(listing_id, similar_ids)
    recommended_price = await pricing_service.calculate_price(
        listing_id=listing_id,
        demand_index=demand_index,
        similar_listing_ids=similar_ids,
    )

    return PriceRecommendation(
        listing_id=listing_id,
        date=target_date,
        demand_index=demand_index,
        recommended_price=recommended_price,
        quality_score=quality_score,
        competition_adjustment=competition_adj,
    )
