from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import uuid

from dependencies import get_db
from services.accommodations import AccommodationsService, get_accommodations_service
from schemas.accommodations import (
    AccommodationCreate,
    AccommodationUpdate,
    AccommodationResponse,
    AccommodationScrapeRequest,
    AccommodationScrapeResponse,
)
from utils.scrapper import scrape_accommodation


accommodations_router = APIRouter(prefix="/api/accommodations", tags=["accommodations"])


@accommodations_router.post("/", response_model=AccommodationResponse, status_code=201)
def create_accommodation(
    data: AccommodationCreate,
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    try:
        return service.create(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating accommodation: {str(e)}")


@accommodations_router.get("/{accommodation_id}", response_model=AccommodationResponse)
def get_accommodation(
    accommodation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    record = service.get_by_id(accommodation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return record


@accommodations_router.get("/", response_model=List[AccommodationResponse])
def list_accommodations(
    itinerary_id: uuid.UUID = Query(..., description="Filter by itinerary UUID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    return service.list_by_itinerary(itinerary_id, skip, limit)


@accommodations_router.put("/{accommodation_id}", response_model=AccommodationResponse)
def update_accommodation(
    accommodation_id: uuid.UUID,
    data: AccommodationUpdate,
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    updated = service.update(accommodation_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return updated


@accommodations_router.delete("/{accommodation_id}", status_code=204)
def soft_delete_accommodation(
    accommodation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    deleted = service.soft_delete(accommodation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return {"message": "Accommodation deleted successfully"}


@accommodations_router.delete("/{accommodation_id}/permanent", status_code=204)
def hard_delete_accommodation(
    accommodation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    success = service.hard_delete(accommodation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return {"message": "Accommodation permanently deleted"}


@accommodations_router.get("/by-itinerary/{itinerary_id}/city/{city}", response_model=List[AccommodationResponse])
def list_accommodations_by_itinerary_and_city(
    itinerary_id: uuid.UUID,
    city: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    service: AccommodationsService = get_accommodations_service(db)
    return service.list_by_itinerary_and_city(itinerary_id, city, skip, limit)


@accommodations_router.post("/scrape", response_model=AccommodationScrapeResponse)
def scrape_accommodation_by_url(payload: AccommodationScrapeRequest):
    try:
        data = scrape_accommodation(str(payload.url))
        return AccommodationScrapeResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error scraping accommodation: {str(e)}")





