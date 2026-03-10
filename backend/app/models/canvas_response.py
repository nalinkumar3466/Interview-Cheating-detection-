from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey,func,UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class CanvasResponse(Base):
    __tablename__ = "canvas_responses"

    __table_args__ = (
        UniqueConstraint("interview_id", "question_id", name="uq_canvas_interview_question"),
    )

    id = Column(Integer, primary_key=True, index=True)

    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    strokes_json = Column(JSONB, nullable=False)
    final_image_base64 = Column(Text, nullable=True)

    # Session metadata
    duration_ms = Column(Integer, nullable=True)
    stroke_count = Column(Integer, nullable=True)

    # Rubric
    structure_score = Column(Float, nullable=True)
    clarity_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    rubric_feedback = Column(Text, nullable=True)

    similarity_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    