from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class OptionStrippingMixin(BaseModel):
    @field_validator('option')
    @classmethod
    def option_must_not_be_empty(cls, v):
        if v is not None and (not v.strip()):
            raise ValueError('Option cannot be empty or only whitespace')
        return v.strip() if v is not None else v

class QuestionOptionBase(OptionStrippingMixin):
    option: str = Field(..., min_length=1, max_length=255, description="The option text")
    description: Optional[str] = Field(None, max_length=500, description="Option description")
    image_url: Optional[str] = Field(None, max_length=500, description="Optional image URL")

class QuestionOptionCreate(QuestionOptionBase):
    question_id: UUID = Field(..., description="ID of the question this option belongs to")

class QuestionOptionUpdate(OptionStrippingMixin):
    option: Optional[str] = Field(None, min_length=1, max_length=255, description="The option text")
    description: Optional[str] = Field(None, max_length=500, description="Option description")
    image_url: Optional[str] = Field(None, max_length=500, description="Optional image URL")

class QuestionOptionResponse(QuestionOptionBase):
    id: UUID
    question_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class QuestionOptionDetailResponse(QuestionOptionResponse):
    question_option_scores: List['QuestionOptionScoreResponse'] = []

    model_config = {"from_attributes": True}

from schemas.traveler_test.question_option_score import QuestionOptionScoreResponse
QuestionOptionDetailResponse.model_rebuild()
