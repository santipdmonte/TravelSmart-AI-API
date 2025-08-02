from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserTravelerTestBase(BaseModel):
    started_at: Optional[datetime] = Field(None, description="When the test was started")

class UserTravelerTestCreate(UserTravelerTestBase):
    user_id: UUID = Field(..., description="ID of the user taking the test")
    traveler_type_id: Optional[UUID] = Field(None, description="ID of the resulting traveler type (set after completion)")

class UserTravelerTestUpdate(BaseModel):
    traveler_type_id: Optional[UUID] = Field(None, description="ID of the resulting traveler type")
    completed_at: Optional[datetime] = Field(None, description="When the test was completed")

class UserTravelerTestResponse(UserTravelerTestBase):
    id: UUID
    user_id: UUID
    traveler_type_id: Optional[UUID]
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if the test is completed"""
        return self.completed_at is not None

    @computed_field
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate test duration in minutes"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return None

    model_config = {"from_attributes": True}

class UserTravelerTestDetailResponse(UserTravelerTestResponse):
    user: Optional['UserResponse'] = None
    traveler_type: Optional['TravelerTypeResponse'] = None
    user_answers: List['UserAnswerResponse'] = []

    model_config = {"from_attributes": True}

class UserTravelerTestComplete(BaseModel):
    traveler_type_id: UUID = Field(..., description="ID of the resulting traveler type")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp (defaults to now)")

class UserTravelerTestStats(BaseModel):
    total_questions: int = Field(..., description="Total number of questions in the test")
    answered_questions: int = Field(..., description="Number of questions answered")
    completion_percentage: float = Field(..., ge=0, le=100, description="Completion percentage")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated minutes to complete")

from schemas.user import UserResponse
from schemas.traveler_test.traveler_type import TravelerTypeResponse
from schemas.traveler_test.user_answers import UserAnswerResponse
UserTravelerTestDetailResponse.model_rebuild()
