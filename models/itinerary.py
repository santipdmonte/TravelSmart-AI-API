from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid
from sqlalchemy.orm import Mapped, mapped_column
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

    itinerary_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, index=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Date] = mapped_column(Date, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=True)
    travelers_count: Mapped[int] = mapped_column(Integer, nullable=True)
    budget: Mapped[float] = mapped_column(Float, nullable=True)
    trip_type: Mapped[str] = mapped_column(String(20), nullable=True)
    tags: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Store as JSON array
    notes: Mapped[Text] = mapped_column(Text, nullable=True)
    details_itinerary: Mapped[JSON] = mapped_column(JSON, nullable=True)
    itinerary_metadata: Mapped[JSON] = mapped_column(JSON, nullable=True)
    trip_name: Mapped[str] = mapped_column(String(200), nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default=VisibilityEnum.PRIVATE.value)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=StatusEnum.DRAFT.value)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    transportation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    def __str__(self):
        return self.trip_name

    def __repr__(self):
        return f"<Itinerary(id={self.itinerary_id}, trip_name='{self.trip_name}', status='{self.status}')>"
