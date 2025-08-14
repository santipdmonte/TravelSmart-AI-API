from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

class UserAnswerBase(BaseModel):
    pass  

class UserAnswerCreate(UserAnswerBase):
    user_traveler_test_id: UUID = Field(..., description="ID of the user traveler test")
    question_option_id: UUID = Field(..., description="ID of the selected question option")

class UserAnswerUpdate(BaseModel):
    question_option_id: Optional[UUID] = Field(None, description="ID of the selected question option")

class UserAnswerResponse(UserAnswerBase):
    id: UUID
    user_traveler_test_id: UUID
    question_option_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class UserAnswerDetailResponse(UserAnswerResponse):
    user_traveler_test: 'UserTravelerTestResponse'
    question_option: 'QuestionOptionResponse'

    model_config = {"from_attributes": True}

class UserAnswerBulkCreate(BaseModel):
    user_traveler_test_id: UUID = Field(..., description="ID of the user traveler test")
    answers: Dict[UUID, List[UUID]] = Field(
        ..., 
        description=(
            "Mapping of question_id -> list of selected question_option_ids. "
            "Supports multi-select by allowing multiple option IDs per question."
        )
    )

from schemas.traveler_test.user_traveler_test import UserTravelerTestResponse
from schemas.traveler_test.question_option import QuestionOptionResponse
UserAnswerDetailResponse.model_rebuild()
