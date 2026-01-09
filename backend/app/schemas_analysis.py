from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AnalysisBase(BaseModel):
    status: str = 'pending'


class AnalysisCreate(AnalysisBase):
    interview_id: int


class AnalysisUpdate(BaseModel):
    status: Optional[str] = None
    event_percentages: Optional[str] = None
    analysis_report: Optional[str] = None
    risk_level: Optional[str] = None
    effective_risk_percentage: Optional[float] = None
    error_message: Optional[str] = None


class AnalysisOut(AnalysisBase):
    id: int
    interview_id: int
    event_percentages: Optional[str] = None
    analysis_report: Optional[str] = None
    risk_level: Optional[str] = None
    effective_risk_percentage: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    interview_id: int
    recording_id: Optional[int] = None
