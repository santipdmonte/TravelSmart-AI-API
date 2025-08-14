from .question import (
    QuestionBase, QuestionCreate, QuestionUpdate, 
    QuestionResponse, QuestionDetailResponse
)
from .question_option import (
    QuestionOptionBase, QuestionOptionCreate, QuestionOptionUpdate,
    QuestionOptionResponse, QuestionOptionDetailResponse
)
from .question_option_score import (
    QuestionOptionScoreBase, QuestionOptionScoreCreate, QuestionOptionScoreUpdate,
    QuestionOptionScoreResponse, QuestionOptionScoreDetailResponse
)
from .traveler_type import (
    TravelerTypeBase, TravelerTypeCreate, TravelerTypeUpdate,
    TravelerTypeResponse, TravelerTypeDetailResponse
)
from .user_answers import (
    UserAnswerBase, UserAnswerCreate, UserAnswerUpdate,
    UserAnswerResponse, UserAnswerDetailResponse, UserAnswerBulkCreate
)
from .user_traveler_test import (
    UserTravelerTestBase, UserTravelerTestCreate, UserTravelerTestUpdate,
    UserTravelerTestResponse, UserTravelerTestDetailResponse,
    UserTravelerTestComplete, UserTravelerTestStats
)

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID

class QuestionWithOptionsResponse(QuestionResponse):
    """Question with its options for displaying the test"""
    question_options: List[QuestionOptionResponse] = []

class TestQuestionnaireResponse(BaseModel):
    """Complete questionnaire for taking the test"""
    questions: List[QuestionWithOptionsResponse] = Field(..., description="List of questions with options")
    total_questions: int = Field(..., description="Total number of questions")
    estimated_time_minutes: int = Field(default=5, description="Estimated time to complete")

class TestSubmissionRequest(BaseModel):
    """Schema for submitting test answers"""
    user_traveler_test_id: UUID = Field(..., description="ID of the test session")
    answers: Dict[UUID, UUID] = Field(..., description="Map of question_id to question_option_id")

class TestResultResponse(BaseModel):
    """Complete test result with traveler type and scores"""
    user_traveler_test: UserTravelerTestResponse
    traveler_type: Optional[TravelerTypeResponse]
    scores: Dict[str, float] = Field(..., description="Scores for each traveler type")
    completion_time_minutes: Optional[float] = None

class TravelerProfileSummary(BaseModel):
    """Summary of a traveler profile for display"""
    id: UUID
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_users: int = Field(default=0, description="Number of users with this profile")

__all__ = [
    "QuestionBase", "QuestionCreate", "QuestionUpdate", 
    "QuestionResponse", "QuestionDetailResponse",
    
    "QuestionOptionBase", "QuestionOptionCreate", "QuestionOptionUpdate",
    "QuestionOptionResponse", "QuestionOptionDetailResponse",
    
    "QuestionOptionScoreBase", "QuestionOptionScoreCreate", "QuestionOptionScoreUpdate",
    "QuestionOptionScoreResponse", "QuestionOptionScoreDetailResponse",
    
    "TravelerTypeBase", "TravelerTypeCreate", "TravelerTypeUpdate",
    "TravelerTypeResponse", "TravelerTypeDetailResponse",
    
    "UserAnswerBase", "UserAnswerCreate", "UserAnswerUpdate",
    "UserAnswerResponse", "UserAnswerDetailResponse", "UserAnswerBulkCreate",
    
    "UserTravelerTestBase", "UserTravelerTestCreate", "UserTravelerTestUpdate",
    "UserTravelerTestResponse", "UserTravelerTestDetailResponse",
    "UserTravelerTestComplete", "UserTravelerTestStats",
    
    "QuestionWithOptionsResponse", "TestQuestionnaireResponse",
    "TestSubmissionRequest", "TestResultResponse", "TravelerProfileSummary"
] 