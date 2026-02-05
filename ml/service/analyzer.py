# ml/service/analyzer.py

import json
import logging

from ml.db.database import SessionLocal
from ml.db.models import InterviewAnalysis

logger = logging.getLogger(__name__)


def store_analysis_result(result: dict):
    try:
        from app.core.database import SessionLocal
        from app.models.analysis import InterviewAnalysis

        session = SessionLocal()

        try:
            # Check if analysis already exists
            analysis = session.query(InterviewAnalysis).filter(
                InterviewAnalysis.interview_id == result["interview_id"]
            ).first()

            if analysis:
                # UPDATE
                analysis.status = "completed"
                analysis.event_percentages = json.dumps(result.get("event_percentages", []))
                analysis.analysis_report = result.get("analysis_report", "")
                analysis.risk_level = result.get("risk_level", "low")
                analysis.effective_risk_percentage = result.get("effective_risk_percentage", 0.0)

            else:
                # CREATE (only if not exists)
                analysis = InterviewAnalysis(
                    interview_id=result["interview_id"],
                    status="completed",
                    event_percentages=json.dumps(result.get("event_percentages", [])),
                    analysis_report=result.get("analysis_report", ""),
                    risk_level=result.get("risk_level", "low"),
                    effective_risk_percentage=result.get("effective_risk_percentage", 0.0)
                )

                session.add(analysis)

            session.commit()
            logger.info(f"✅ Analysis stored for interview {result['interview_id']}")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"❌ Backend DB failed: {e}")
