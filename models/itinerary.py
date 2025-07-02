from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid
from database import Base


class VisibilityEnum(enum.Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class StatusEnum(enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"


class TripTypeEnum(enum.Enum):
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


class Itinerary(Base):
    __tablename__ = "itineraries"

    itinerary_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    slug = Column(String(255), nullable=True, unique=True, index=True)
    destination = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    duration_days = Column(Integer, nullable=True)
    travelers_count = Column(Integer, nullable=True)
    budget = Column(Float, nullable=True)
    trip_type = Column(String(20), nullable=True)
    tags = Column(JSON, nullable=True)  # Store as JSON array
    notes = Column(Text, nullable=True)
    details_itinerary = Column(JSON, nullable=True)
    trip_name = Column(String(200), nullable=False)
    visibility = Column(String(20), nullable=False, default=VisibilityEnum.PRIVATE.value)
    status = Column(String(20), nullable=False, default=StatusEnum.DRAFT.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __str__(self):
        return self.trip_name

    def __repr__(self):
        return f"<Itinerary(id={self.itinerary_id}, trip_name='{self.trip_name}', status='{self.status}')>"
