from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Recording(Base):
    __tablename__ = 'recordings'
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=True)
    file_path = Column(String, nullable=True)
    answer_text = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
