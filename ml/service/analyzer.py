# ml/service/analyzer.py

import json
from pathlib import Path
from ml.service.event_percentage_calculator import convert_events_to_percentages
from ml.service.risk_calculator import (
    compute_effective_risk_percentage,
    classify_risk_level
)
from ml.service.llm_client import generate_llm_analysis

from ml.db.database import SessionLocal
from ml.db.models import InterviewAnalysis


class InterviewAnalysisService:

    def analyze_from_event_json(
        self,
        event_json_path: str,
        video_duration: float,
        video_id: str
    ) -> dict:
        """
        Entry point AFTER behavior detection.
        """


        event_percentages = convert_events_to_percentages(
            event_json_path="ml/events/interviewsample1_events.json",
            video_duration=video_duration
        )

        effective_percentage = compute_effective_risk_percentage(event_percentages)

        risk_level = classify_risk_level(effective_percentage)

        analysis_report = generate_llm_analysis(event_percentages, risk_level)

        return {
            "video_id": video_id,
            "event_percentages": event_percentages,
            "analysis_report": analysis_report
        }

def store_analysis_result(result):
    session = SessionLocal()

    record = InterviewAnalysis(
        video_id=result["video_id"],
        event_percentages=result["event_percentages"],
        analysis_report=result["analysis_report"],
        risk_level=result["analysis_report"].split("Overall Risk Level:")[-1].strip()
    )

    session.add(record)
    session.commit()
    session.close()

