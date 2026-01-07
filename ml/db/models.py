from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from ml.db.database import Base

class InterviewAnalysis(Base):
    __tablename__ = "interview_analysis"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, index=True)
    event_percentages = Column(Text)
    analysis_report = Column(Text)
    risk_level = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

