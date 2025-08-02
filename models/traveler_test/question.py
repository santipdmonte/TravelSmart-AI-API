from database import Base
from sqlalchemy import String, Integer, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    question_options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(trim(question)) > 0", name="check_question_not_empty"),
        CheckConstraint("\"order\" > 0", name="check_question_order_positive"),
    )

    def __str__(self):
        return self.question

    def __repr__(self):
        return f"<Question(id={self.id}, order={self.order}, question='{self.question[:50]}...')>"
    
    