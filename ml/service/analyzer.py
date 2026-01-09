# ml/service/analyzer.py

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def store_analysis_result_ml_db(result: dict):
    """Store analysis in ML database (SQLite)"""
    try:
        from ml.db.database import SessionLocal
        from ml.db.models import InterviewAnalysis
        
        session = SessionLocal()
        try:
            record = InterviewAnalysis(
                video_id=result.get("video_id", "unknown"),
                event_percentages=json.dumps(result.get("event_percentages", {})),
                analysis_report=result.get("analysis_report", ""),
                risk_level=result.get("risk_level", "unknown")
            )
            session.add(record)
            session.commit()
            logger.info("Analysis result stored in ML database!")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    except ImportError:
        logger.warning("ML database not available, skipping ML DB storage")


def store_analysis_result(result: dict):
    """
    Store analysis in backend database.
    
    Args:
        result: dict containing:
            - interview_id: int
            - video_id: str
            - event_percentages: dict
            - analysis_report: str
            - risk_level: str
            - effective_risk_percentage: float
    """
    try:
        from app.core.database import SessionLocal
        from app.models.analysis import InterviewAnalysis
        
        session = SessionLocal()
        try:
            record = InterviewAnalysis(
                interview_id=result["interview_id"],
                status="completed",
                event_percentages=json.dumps(result.get("event_percentages", {})),
                analysis_report=result.get("analysis_report", ""),
                risk_level=result.get("risk_level", "medium"),
                effective_risk_percentage=result.get("effective_risk_percentage", 0.0)
            )
            session.add(record)
            session.commit()
            logger.info(f"Analysis stored for interview {result['interview_id']}")
        except Exception as e:
            session.rollback()
            logger.exception(f"Error storing analysis: {e}")
            raise
        finally:
            session.close()
    except ImportError as e:
        logger.warning(f"Backend database not available: {e}, trying ML DB instead")
        store_analysis_result_ml_db(result)


