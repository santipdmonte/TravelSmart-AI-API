from database import Base
from sqlalchemy import String, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class TravelerType(Base):
    __tablename__ = "traveler_types"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    prompt_description: Mapped[str] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    question_option_scores = relationship("QuestionOptionScore", back_populates="traveler_type", cascade="all, delete-orphan")
    user_tests = relationship("UserTravelerTest", back_populates="traveler_type")
    users = relationship("User", back_populates="traveler_type")

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="check_traveler_type_name_not_empty"),
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<TravelerType(id={self.id}, name='{self.name}')>"
    
    