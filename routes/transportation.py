from fastapi import APIRouter, Depends, HTTPException

from schemas.transportation import TransportationCreate, TransportationResponse, TransportationUpdate
from services.transportation import TransportationServices
from sqlalchemy.orm import Session
from dependencies import get_db
from typing import List
from uuid import UUID


transportation_router = APIRouter(prefix="/api/transports", tags=["transports"])

@transportation_router.post("/", response_model=TransportationResponse, status_code=201)
def create_transportation(
    transportation_data: TransportationCreate,
    itinerary_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        return TransportationServices(db).create_transportation(transportation_data, itinerary_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating transportation: {str(e)}")

@transportation_router.get("/", response_model=List[TransportationResponse])
def get_all_transportations(
    db: Session = Depends(get_db)
):
    try:
        return TransportationServices(db).get_all_transportations()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting all transportations: {str(e)}")

@transportation_router.get("/{transportation_id}", response_model=TransportationResponse)
def get_transportation_by_id(
    transportation_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        return TransportationServices(db).get_transportation_by_id(transportation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting transportation by id: {str(e)}")

@transportation_router.get("/itinerary/{itinerary_id}", response_model=List[TransportationResponse])
def get_transportation_by_itinerary_id(
    itinerary_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        return TransportationServices(db).get_transportation_by_itinerary_id(itinerary_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting transportation by itinerary id: {str(e)}")

@transportation_router.put("/{transportation_id}", response_model=TransportationResponse)
def update_transportation(
    transportation_id: UUID,
    transportation_data: TransportationUpdate,
    db: Session = Depends(get_db)
):
    try:
        return TransportationServices(db).update_transportation(transportation_id, transportation_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating transportation: {str(e)}")

@transportation_router.delete("/{transportation_id}", status_code=204)
def delete_transportation(
    transportation_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        return TransportationServices(db).delete_transportation(transportation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting transportation: {str(e)}")