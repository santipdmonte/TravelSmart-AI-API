from sqlalchemy import Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional
import uuid
from database import Base


class ItineraryChangeLog(Base):
    __tablename__ = "itinerary_change_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    itinerary_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("itineraries.itinerary_id", ondelete="CASCADE"), index=True)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
