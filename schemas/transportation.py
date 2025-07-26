from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID

class TransportationBase(BaseModel):
    transportation_details: str

class TransportationCreate(TransportationBase):
    # itinerary_id: UUID
    pass

class TransportationUpdate(TransportationBase):
    pass

class TransportationResponse(TransportationBase):
    id: UUID
    transportation_details: str