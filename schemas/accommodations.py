from pydantic import BaseModel, Field, AnyUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class AccommodationCreate(BaseModel):
    itinerary_id: UUID = Field(..., description="Related itinerary UUID")
    city: str = Field(..., max_length=255, description="City of the accommodation candidate")
    url: AnyUrl = Field(..., description="Accommodation URL")


class AccommodationUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Optional title")
    description: Optional[str] = Field(None, description="Optional description")
    img_urls: Optional[List[AnyUrl]] = Field(None, description="List of image URLs")
    provider: Optional[str] = Field(None, max_length=100, description="Provider name, e.g., Airbnb, Booking")
    status: Optional[str] = Field(None, description="draft, confirmed, deleted")


class AccommodationResponse(BaseModel):
    id: UUID
    itinerary_id: UUID
    city: str
    url: AnyUrl
    title: Optional[str]
    description: Optional[str]
    img_urls: List[AnyUrl] = Field(default_factory=list)
    provider: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

