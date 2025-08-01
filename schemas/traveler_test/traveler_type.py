from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class StrippedNameValidator(BaseModel):
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError('Name cannot be empty or only whitespace')
            return stripped
        return v

class TravelerTypeBase(StrippedNameValidator):
    name: str = Field(..., min_length=1, max_length=255, description="Traveler type name")
    description: Optional[str] = Field(None, max_length=500, description="Traveler type description")
    prompt_description: Optional[str] = Field(None, max_length=1000, description="Description for AI prompts")
    image_url: Optional[str] = Field(None, max_length=500, description="Optional image URL")

class TravelerTypeCreate(TravelerTypeBase):
    pass

class TravelerTypeUpdate(StrippedNameValidator):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Traveler type name")
    description: Optional[str] = Field(None, max_length=500, description="Traveler type description")
    prompt_description: Optional[str] = Field(None, max_length=1000, description="Description for AI prompts")
    image_url: Optional[str] = Field(None, max_length=500, description="Optional image URL")

class TravelerTypeResponse(TravelerTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TravelerTypeDetailResponse(TravelerTypeResponse):
    question_option_scores: List['QuestionOptionScoreResponse'] = []
    user_tests: List['UserTravelerTestResponse'] = []

    model_config = {"from_attributes": True}

from schemas.traveler_test.question_option_score import QuestionOptionScoreResponse
from schemas.traveler_test.user_traveler_test import UserTravelerTestResponse
TravelerTypeDetailResponse.model_rebuild()
