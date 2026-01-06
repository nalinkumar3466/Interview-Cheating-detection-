from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class InterviewAnalysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True)
    video_id = Column(String)
    event_percentages = Column(JSON)
    analysis_report = Column(Text)
    risk_level = Column(String)
    created_at = Column(DateTime, default=func.now())
