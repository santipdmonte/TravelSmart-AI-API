from database import Base
from sqlalchemy import ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_traveler_test_id: Mapped[UUID] = mapped_column(ForeignKey("user_traveler_tests.id", ondelete="CASCADE"), nullable=False)
    question_option_id: Mapped[UUID] = mapped_column(ForeignKey("question_options.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user_traveler_test = relationship("UserTravelerTest", back_populates="user_answers")
    question_option = relationship("QuestionOption", back_populates="user_answers")

    def __str__(self):
        return f"Answer for option {self.question_option_id}"

    def __repr__(self):
        return f"<UserAnswer(id={self.id}, test_id={self.user_traveler_test_id}, option_id={self.question_option_id})>"
    
    