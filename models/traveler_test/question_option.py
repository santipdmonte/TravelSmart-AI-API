from database import Base
from sqlalchemy import String, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    question = relationship("Question", back_populates="question_options")
    question_option_scores = relationship("QuestionOptionScore", back_populates="question_option", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="question_option")

    __table_args__ = (
        CheckConstraint("length(trim(option)) > 0", name="check_option_not_empty"),
    )

    def __str__(self):
        return self.option

    def __repr__(self):
        return f"<Option(id={self.id}, option='{self.option}')>"