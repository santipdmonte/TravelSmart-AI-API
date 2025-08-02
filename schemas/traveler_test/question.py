from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class StrippedQuestionValidator(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500, description="The question text")

    @field_validator('question')
    @classmethod
    def question_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError('Question cannot be empty or only whitespace')
            return stripped
        return v

class QuestionBase(StrippedQuestionValidator):
    question: str = Field(..., min_length=1, max_length=500, description="The question text")
    order: Optional[int] = Field(None, gt=0, description="Question order (must be positive if provided)")
    category: Optional[str] = Field(None, max_length=255, description="Question category")
    image_url: Optional[str] = Field(None, max_length=500, description="Optional image URL")

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(StrippedQuestionValidator):
    order: Optional[int] = Field(None, gt=0, description="Question order (must be positive)")
    category: Optional[str] = Field(None, max_length=255, description="Question category")
    image_url: Optional[str] = Field(None, max_length=500, description="Optional image URL")

class QuestionResponse(QuestionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class QuestionDetailResponse(QuestionResponse):
    question_options: List['QuestionOptionResponse'] = []

    model_config = {"from_attributes": True}

from schemas.traveler_test.question_option import QuestionOptionResponse
QuestionDetailResponse.model_rebuild()
