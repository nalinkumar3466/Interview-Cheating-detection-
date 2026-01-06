from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class InterviewBase(BaseModel):
    title: str
    candidate_name: str
    candidate_email: EmailStr
    scheduled_at: datetime
    duration_minutes: int
    timezone: Optional[str] = None
    instructions: Optional[str] = None


class QuestionPayload(BaseModel):
    id: Optional[int] = None
    order: int = Field(..., ge=0)
    text: str
    examples: Optional[str] = None
    type: Optional[str] = None


class InterviewCreate(InterviewBase):
    questions: List[QuestionPayload]
    token_ttl_minutes: Optional[int] = None


class Interview(InterviewBase):
    id: int

    class Config:
        from_attributes = True


class InterviewOut(BaseModel):
    id: int
    title: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    timezone: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Question(QuestionPayload):
    id: int
    interview_id: int

    class Config:
        from_attributes = True



class RecordingBase(BaseModel):
    answer_text: str | None = None


class RecordingCreate(RecordingBase):
    question_id: int | None = None


class Recording(RecordingBase):
    id: int
    interview_id: int
    question_id: int | None = None
    file_path: str

    class Config:
        from_attributes = True
