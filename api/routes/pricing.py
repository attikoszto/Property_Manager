from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.dependencies import (
    get_demand_service,
    get_listing_repo,
    get_pricing_service,
    get_similarity_service,
)
from infrastructure.database.repository import ListingRepository
from services.demand_service import DemandService
from services.pricing_service import PricingService
from services.similarity_service import SimilarityService

router = APIRouter()


class PriceRecommendation(BaseModel):
    listing_id: int
    date: date
    demand_index: float
    recommended_price: float
    quality_score: float
    competition_adjustment: float
    checkin_adjustment: float


@router.get("/recommendation", response_model=PriceRecommendation)
async def get_price_recommendation(
    listing_id: int = Query(...),
    target_date: date = Query(default_factory=date.today),
    checkin_date: date | None = Query(default=None),
    include_weighted_customers: bool = Query(default=False),
    pricing_service: PricingService = Depends(get_pricing_service),
    demand_service: DemandService = Depends(get_demand_service),
    similarity_service: SimilarityService = Depends(get_similarity_service),
    listing_repo: ListingRepository = Depends(get_listing_repo),
):
    listing = await listing_repo.get_by_id(listing_id)
    similar_ids = await similarity_service.find_similar(
        listing_id,
        exclude_customers=True,
        exclude_owner_id=listing.owner_id,
    )

    # Optionally include customer listings at reduced weight (high market penetration)
    customer_ids: list[int] | None = None
    if include_weighted_customers:
        customer_ids = await similarity_service.find_similar_customers(
            listing_id,
            exclude_owner_id=listing.owner_id,
        )

    demand_index = await demand_service.compute_demand_index(
        target_date=target_date,
        location="Berchtesgaden",
        listing_ids=similar_ids,
    )
    quality_score = await pricing_service.compute_quality_score(listing_id)
    competition_adj = await pricing_service.compute_competition_adjustment(
        listing_id, similar_ids, customer_ids
    )
    checkin_adj = pricing_service.compute_checkin_adjustment(checkin_date) if checkin_date else 1.0
    recommended_price = await pricing_service.calculate_price(
        listing_id=listing_id,
        demand_index=demand_index,
        similar_listing_ids=similar_ids,
        customer_listing_ids=customer_ids,
        checkin_date=checkin_date,
    )

    return PriceRecommendation(
        listing_id=listing_id,
        date=target_date,
        demand_index=demand_index,
        recommended_price=recommended_price,
        quality_score=quality_score,
        competition_adjustment=competition_adj,
        checkin_adjustment=checkin_adj,
    )
