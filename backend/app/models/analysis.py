from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class InterviewAnalysis(Base):
    __tablename__ = 'interview_analysis'
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False, index=True)
    status = Column(String, default='pending')  # pending, processing, completed, failed
    event_percentages = Column(Text, nullable=True)  # JSON string
    analysis_report = Column(Text, nullable=True)
    risk_level = Column(String, nullable=True)  # low, medium, high
    effective_risk_percentage = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
