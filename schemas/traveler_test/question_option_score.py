from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class QuestionOptionScoreBase(BaseModel):
    score: int = Field(..., ge=-10, le=10, description="Score value (range: -10 to 10)")

class QuestionOptionScoreCreate(QuestionOptionScoreBase):
    question_option_id: UUID = Field(..., description="ID of the question option")
    traveler_type_id: UUID = Field(..., description="ID of the traveler type")

class QuestionOptionScoreUpdate(BaseModel):
    score: Optional[int] = Field(None, ge=-10, le=10, description="Score value (range: -10 to 10)")

class QuestionOptionScoreResponse(QuestionOptionScoreBase):
    id: UUID
    question_option_id: UUID
    traveler_type_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class QuestionOptionScoreDetailResponse(QuestionOptionScoreResponse):
    question_option: 'QuestionOptionResponse'
    traveler_type: 'TravelerTypeResponse'

    model_config = {"from_attributes": True}

from schemas.traveler_test.question_option import QuestionOptionResponse
from schemas.traveler_test.traveler_type import TravelerTypeResponse
QuestionOptionScoreDetailResponse.model_rebuild()
