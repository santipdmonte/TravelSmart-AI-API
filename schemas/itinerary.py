from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum
import uuid
from schemas.traveler_test.traveler_type import TravelerTypeResponse


class VisibilityEnum(str, Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class StatusEnum(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"


class TripTypeEnum(str, Enum):
    BUSINESS = "business"
    LEISURE = "leisure"
    ADVENTURE = "adventure"
    FAMILY = "family"
    ROMANTIC = "romantic"
    CULTURAL = "cultural"
    BACKPACKING = "backpacking"
    LUXURY = "luxury"
    BUDGET = "budget"
    SOLO = "solo"
    GROUP = "group"


class ItineraryBase(BaseModel):
    """Base schema with common fields"""
    user_id: Optional[str] = Field(None, max_length=255, description="Auth0 user identifier, nullable for guest sessions")
    session_id: Optional[uuid.UUID] = Field(None, description="UUID session identifier for guest users")
    trip_name: str = Field(..., max_length=200, description="Name of the trip")
    duration_days: Optional[int] = Field(None, ge=1, description="Duration of the trip in days")
    start_date: Optional[date] = Field(None, description="Trip start date")
    travelers_count: Optional[int] = Field(None, ge=1, description="Number of travelers")
    itinerary_metadata: Optional[Dict[str, Any]] = Field(None, description="JSON field containing itinerary metadata")
    details_itinerary: Optional[Dict[str, Any]] = Field(None, description="JSON field containing itinerary details")
    notes: Optional[str] = Field(None, description="Private notes for the traveler")
    visibility: VisibilityEnum = Field(default=VisibilityEnum.PRIVATE, description="Visibility level of the itinerary")
    status: StatusEnum = Field(default=StatusEnum.DRAFT, description="Status of the itinerary")
    # trip_type: Optional[TripTypeEnum] = Field(None, description="Type of trip")
    # tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    # destination: Optional[str] = Field(None, description="Primary destination of the trip")
    # slug: Optional[str] = Field(None, description="URL-friendly identifier for sharing")
    # budget: Optional[float] = Field(None, ge=0, description="Trip budget")
    # transportation_id: Optional[uuid.UUID] = Field(None, description="UUID identifier of the associated transportation")

    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class ItineraryCreate(BaseModel):
    """Schema for creating a new itinerary"""
    # Remove user_id and session_id - they'll be automatically assigned
    slug: Optional[str] = Field(None, description="URL-friendly identifier for sharing")
    destination: Optional[str] = Field(None, description="Primary destination of the trip")
    start_date: Optional[date] = Field(None, description="Trip start date")
    duration_days: Optional[int] = Field(None, ge=1, description="Duration of the trip in days")
    travelers_count: Optional[int] = Field(None, ge=1, description="Number of travelers")
    budget: Optional[float] = Field(None, ge=0, description="Trip budget")
    trip_type: Optional[TripTypeEnum] = Field(None, description="Type of trip")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    notes: Optional[str] = Field(None, description="Private notes for the traveler")
    details_itinerary: Optional[Dict[str, Any]] = Field(None, description="JSON field containing itinerary details")
    trip_name: str = Field(..., max_length=200, description="Name of the trip")
    visibility: VisibilityEnum = Field(default=VisibilityEnum.PRIVATE, description="Visibility level of the itinerary")
    status: StatusEnum = Field(default=StatusEnum.DRAFT, description="Status of the itinerary")
    # transportation_id: Optional[uuid.UUID] = Field(None, description="UUID identifier of the associated transportation")

    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class ItineraryUpdate(BaseModel):
    """Schema for updating an existing itinerary"""
    slug: Optional[str] = Field(None, description="URL-friendly identifier for sharing")
    destination: Optional[str] = Field(None, description="Primary destination of the trip")
    start_date: Optional[date] = Field(None, description="Trip start date")
    duration_days: Optional[int] = Field(None, ge=1, description="Duration of the trip in days")
    travelers_count: Optional[int] = Field(None, ge=1, description="Number of travelers")
    budget: Optional[float] = Field(None, ge=0, description="Trip budget")
    trip_type: Optional[TripTypeEnum] = Field(None, description="Type of trip")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    notes: Optional[str] = Field(None, description="Private notes for the traveler")
    details_itinerary: Optional[Dict[str, Any]] = Field(None, description="JSON field containing itinerary details")
    trip_name: Optional[str] = Field(None, max_length=200, description="Name of the trip")
    visibility: Optional[VisibilityEnum] = Field(None, description="Visibility level of the itinerary")
    status: Optional[StatusEnum] = Field(None, description="Status of the itinerary")
    itinerario_diario: Optional[List[Dict[str, Any]]] = Field(None, description="JSON field containing itinerary daily details")
    # transportation_id: Optional[uuid.UUID] = Field(None, description="UUID identifier of the associated transportation")

    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }

class ItineraryPreferences(BaseModel):
    """Schema for itinerary preferences"""
    when: Optional[str] = Field(None, description="When the trip is happening")
    trip_type: Optional[str] = Field(None, description="Type of trip")
    occasion: Optional[str] = Field(None, description="Occasion of the trip")
    city_view: Optional[str] = Field(None, description="City view")
    travel_styles: Optional[List[str]] = Field(None, description="Travel styles")
    food_preferences: Optional[List[str]] = Field(None, description="Food preferences")
    budget: Optional[str] = Field(None, description="Budget type") # Economico, Intermedio, Confort, Lujo
    travel_pace: Optional[str] = Field(None, description="Travel pace") # Relax, Equilibrado, Activo
    goal: Optional[str] = Field(None, description="Goal of the trip")
    notes: Optional[str] = Field(None, description="Notes")

class ItineraryGenerate(BaseModel):
    """Schema for generating an itinerary"""
    trip_name: str = Field(..., max_length=200, description="Name of the trip")
    duration_days: int = Field(..., ge=1, description="Duration of the trip in days")
    # Optional traveler profile to personalize generation (filled server-side from Traveler Test)
    traveler_origin: Optional[str] = Field(None, description="Origin of the traveler")
    traveler_profile_name: Optional[str] = Field(None, description="Latest traveler type name for the user")
    traveler_profile_desc: Optional[str] = Field(None, description="Description used to steer itinerary generation")
    preferences: Optional[ItineraryPreferences] = Field(None, description="Preferences for the itinerary generation")


class ItineraryResponse(ItineraryBase):
    """Schema for itinerary responses - works with SQLAlchemy ORM"""
    itinerary_id: uuid.UUID = Field(..., description="Primary key UUID identifier for the itinerary")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    # traveler_profile: Optional[TravelerTypeResponse] = Field(None, description="Resolved traveler type used to personalize this itinerary")

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility (Pydantic V2)
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


class ItineraryList(BaseModel):
    """Schema for listing itineraries - works with SQLAlchemy ORM"""
    itinerary_id: uuid.UUID = Field(..., description="Primary key UUID identifier")
    user_id: Optional[str] = Field(None, description="Auth0 user identifier")
    session_id: Optional[uuid.UUID] = Field(None, description="UUID session identifier")
    slug: Optional[str] = Field(None, description="URL-friendly identifier")
    destination: Optional[str] = Field(None, description="Primary destination")
    start_date: Optional[date] = Field(None, description="Trip start date")
    duration_days: Optional[int] = Field(None, description="Duration in days")
    trip_name: str = Field(..., description="Name of the trip")
    trip_type: Optional[TripTypeEnum] = Field(None, description="Type of trip")
    visibility: VisibilityEnum = Field(..., description="Visibility level")
    status: StatusEnum = Field(..., description="Status of the itinerary")
    # transportation_id: Optional[uuid.UUID] = Field(None, description="UUID identifier of the associated transportation")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility (Pydantic V2)
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }
