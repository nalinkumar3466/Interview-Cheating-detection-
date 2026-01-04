from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class CandidateLog(Base):
    __tablename__ = 'candidate_logs'
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, nullable=True, index=True)
    token = Column(String(128), nullable=True, index=True)
    event = Column(String(128), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
