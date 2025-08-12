from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ChangeLogCreate(BaseModel):
    itinerary_id: uuid.UUID
    user_prompt: str
    ai_response_summary: Optional[str] = Field(default=None)


class ChangeLogResponse(BaseModel):
    id: uuid.UUID
    itinerary_id: uuid.UUID
    user_prompt: str
    ai_response_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
