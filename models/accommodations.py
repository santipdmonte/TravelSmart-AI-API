from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Accommodations(Base):
    __tablename__ = "accommodations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    itinerary_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("itineraries.itinerary_id", ondelete="CASCADE"), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    img_urls: Mapped[JSON] = mapped_column(JSON, nullable=False, server_default="[]")
    provider: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("itinerary_id", "url", name="uq_accommodations_itinerary_url"),
    )

