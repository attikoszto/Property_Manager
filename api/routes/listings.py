from fastapi import APIRouter, Depends
from pydantic import BaseModel

from infrastructure.database.repository import ListingRepository
from infrastructure.database.models import ListingModel
from api.dependencies import get_listing_repo

router = APIRouter()


class ListingCreate(BaseModel):
    external_id: str
    platform: str
    title: str
    location: str
    lat: float
    lng: float
    capacity: int
    bedrooms: int
    bathrooms: int
    square_meters: float
    rating: float = 0.0
    review_count: int = 0
    amenities: list[str] = []
    base_price: float
    owner_id: str | None = None


class ListingResponse(BaseModel):
    id: int
    external_id: str
    platform: str
    title: str
    location: str
    lat: float
    lng: float
    capacity: int
    bedrooms: int
    bathrooms: int
    square_meters: float
    rating: float
    review_count: int
    amenities: list[str] | None
    base_price: float
    owner_id: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ListingResponse])
async def get_listings(
    listing_repo: ListingRepository = Depends(get_listing_repo),
):
    return await listing_repo.get_all()


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: int,
    listing_repo: ListingRepository = Depends(get_listing_repo),
):
    return await listing_repo.get_by_id(listing_id)


@router.post("/", response_model=ListingResponse)
async def create_listing(
    data: ListingCreate,
    listing_repo: ListingRepository = Depends(get_listing_repo),
):
    listing = ListingModel(**data.model_dump())
    return await listing_repo.upsert(listing)
