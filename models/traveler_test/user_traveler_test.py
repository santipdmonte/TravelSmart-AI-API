from database import Base
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserTravelerTest(Base):
    __tablename__ = "user_traveler_tests"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    traveler_type_id: Mapped[UUID] = mapped_column(ForeignKey("traveler_types.id", ondelete="RESTRICT"), nullable=False)
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    traveler_type = relationship("TravelerType", back_populates="user_tests")
    user_answers = relationship("UserAnswer", back_populates="user_traveler_test", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("completed_at IS NULL OR completed_at >= started_at", name="check_completion_after_start"),
        UniqueConstraint('user_id', 'started_at', name='uq_user_test_session'),  # Prevent duplicate test sessions
    )

    @property
    def is_completed(self):
        return self.completed_at is not None

    @property
    def duration_minutes(self):
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return None

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"Traveler Test ({status})"

    def __repr__(self):
        return f"<UserTravelerTest(id={self.id}, user_id={self.user_id}, completed={self.is_completed})>"
    
    