from database import Base
from sqlalchemy import Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class QuestionOptionScore(Base):
    __tablename__ = "question_option_scores"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_option_id: Mapped[UUID] = mapped_column(ForeignKey("question_options.id", ondelete="CASCADE"), nullable=False)
    traveler_type_id: Mapped[UUID] = mapped_column(ForeignKey("traveler_types.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    question_option = relationship("QuestionOption", back_populates="question_option_scores")
    traveler_type = relationship("TravelerType", back_populates="question_option_scores")
    
    __table_args__ = (
        UniqueConstraint('question_option_id', 'traveler_type_id', name='uq_question_option_travelertype'),
        CheckConstraint("score >= -10 AND score <= 10", name="check_score_range"),
    )

    def __repr__(self):
        return f"<QuestionOptionScore(question_option_id={self.question_option_id}, traveler_type_id={self.traveler_type_id}, score={self.score})>"

