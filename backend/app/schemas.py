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


# === CANVAS DRAWING SCHEMAS ===

class StrokePoint(BaseModel):
    """A single point in a canvas stroke."""
    x: float
    y: float
    t: int  # Timestamp in milliseconds


class Stroke(BaseModel):
    """A single drawing stroke on the canvas."""
    id: str
    tool: str  # "pen", "eraser"
    color: str  # Hex color code
    strokeWidth: int
    startedAt: int  # Timestamp in milliseconds
    points: List[StrokePoint]


class CanvasSubmitPayload(BaseModel):
    """Canvas drawing submission from frontend."""
    question_id: int
    strokes: List[Stroke]
    final_image: str  # Base64-encoded PNG
    duration: int  # Duration in seconds
    stroke_count: int


class CanvasResponseOut(BaseModel):
    """Canvas response retrieved from database."""
    
    id: int
    interview_id: int
    question_id: int
    strokes_json: Optional[List] = None
    final_image_base64: str = None
    duration_ms: int | None = None
    stroke_count: int | None = None
    session_metadata: Optional[dict] = None
    structure_score: Optional[float] = None
    clarity_score: Optional[float] = None
    completeness_score: Optional[float] = None
    overall_score: Optional[float] = None
    rubric_feedback: Optional[str] = None
    similarity_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CanvasRubric(BaseModel):
    """Rubric for grading canvas drawings."""
    structure_score: float = Field(..., ge=0, le=5)  # 0-5
    clarity_score: float = Field(..., ge=0, le=5)    # 0-5
    completeness_score: float = Field(..., ge=0, le=5)  # 0-5
    feedback: Optional[str] = None