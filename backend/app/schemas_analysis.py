from pydantic import BaseModel
from typing import List, Optional


class EventOut(BaseModel):
    label: str
    timestamp: float


class AnalysisOut(BaseModel):
    status: str
    risk_level: Optional[str] = None
    event_percentages: List[dict] = []
    analysis_report: Optional[str] = None
    events: List[EventOut] = []
