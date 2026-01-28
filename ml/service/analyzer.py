# ml/service/analyzer.py

import json
import logging

from ml.db.database import SessionLocal
from ml.db.models import InterviewAnalysis

logger = logging.getLogger(__name__)


def store_analysis_result(result: dict):
    """
    Store analysis result in Postgres DB (main database)
    """

    session = SessionLocal()

    try:
        record = InterviewAnalysis(

            # IMPORTANT: must match DB column
            interview_id=result["interview_id"],

            status="completed",

            event_percentages=json.dumps(
                result.get("event_percentages", [])
            ),

            analysis_report=result.get("analysis_report", ""),

            risk_level=result.get("risk_level", "medium"),

            effective_risk_percentage=result.get(
                "effective_risk_percentage", 0.0
            ),

            error_message=None,
        )

        session.add(record)
        session.commit()

        logger.info(
            f"✅ Analysis stored for interview {result['interview_id']}"
        )

    except Exception as e:

        session.rollback()

        logger.error(f"❌ DB insert failed: {e}")

        raise e

    finally:
        session.close()
