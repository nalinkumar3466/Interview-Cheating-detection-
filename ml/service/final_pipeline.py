import os
import glob
import csv
import json
import sys
import logging
from dotenv import load_dotenv
import os

load_dotenv()

from pathlib import Path
# Ensure backend is on PYTHONPATH for subprocess runs
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = PROJECT_ROOT / "backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))


from ml.temporal_smoothing import analyze_single_video
from ml.process_behavior_from_csv import (
    BehaviorRulesFromCSV,
    SuspiciousEventManager
)

from ml.service.event_percentage_calculator import convert_events_to_percentages
from ml.service.llm_client import generate_llm_analysis
from ml.service.analyzer import store_analysis_result

from ml.service.risk_calculator import (
    compute_effective_risk_percentage,
    classify_risk_level
)


# ==============================
# LOGGING SETUP
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================
# CONFIG
# ==============================
UPLOADS_DIR = os.path.join("backend", "uploads")
LOGS_DIR = "logs"
EVENTS_DIR = "events"

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(EVENTS_DIR, exist_ok=True)

# ==============================
# MAIN PIPELINE
# ==============================
def analyze_interview(video_path: str, interview_id: int) -> dict:
    """
    Analyze a single interview video file.
    
    Args:
        video_path: Full path to video file
        interview_id: Backend interview ID for storing results
    
    Returns:
        dict with analysis results or error details
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        video_name = os.path.basename(video_path)
        video_id = f"interview_{interview_id}"
        
        logger.info(f"Starting analysis for interview {interview_id}: {video_name}")
        
        # --------------------------------------------------
        # STEP 1: VIDEO → CSV + RAW EVENTS
        # --------------------------------------------------
        logger.info(f"Step 1: Analyzing video {video_path}")
        _, video_duration, csv_path = analyze_single_video(video_path)
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV not generated: {csv_path}")
        
        logger.info(f"Video duration: {video_duration}s, CSV path: {csv_path}")
        
        # --------------------------------------------------
        # STEP 2: CSV → BEHAVIOR EVENTS
        # --------------------------------------------------
        logger.info("Step 2: Processing behavior events from CSV")
        event_manager = SuspiciousEventManager()
        fps = 30  # timestamps already in seconds
        
        behavior = BehaviorRulesFromCSV(fps=fps, event_manager=event_manager)
        
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gaze = row.get("Smooth_gaze", "CENTER")
                t = float(row["Timestamp"])
                blink_flag = row.get("Warmup_Frames", "NONE")
                behavior.update(gaze, t, blink_flag)
        
        behavior.finalize()
        
        event_json_path = os.path.join(EVENTS_DIR, f"{video_id}_events.json")
        event_manager.save(event_json_path)
        
        logger.info(f"Events saved to {event_json_path}")
        
        # --------------------------------------------------
        # STEP 3: EVENTS → % EXPOSURE
        # --------------------------------------------------
        logger.info("Step 3: Computing event percentages")
        event_percentages = convert_events_to_percentages(
            event_json_path=event_json_path,
            video_duration=video_duration
        )
        
        # --------------------------------------------------
        # STEP 4: EFFECTIVE RISK
        # --------------------------------------------------
        logger.info("Step 4: Computing effective risk")
        effective_percentage = compute_effective_risk_percentage(event_percentages)
        risk_level = classify_risk_level(effective_percentage)
        
        logger.info(f"Risk level: {risk_level}, Effective %: {effective_percentage:.2f}%")
        
        # --------------------------------------------------
        # STEP 5: LLM ANALYSIS
        # --------------------------------------------------
        logger.info("Step 5: Generating LLM analysis")
        analysis_report = generate_llm_analysis(event_percentages, risk_level)
        
        # --------------------------------------------------
        # STEP 6: STORE IN DATABASE
        # --------------------------------------------------
        logger.info("Step 6: Storing analysis in database")
        video_id = f"interview_{interview_id}"
        result = {
            "interview_id": interview_id, 
            "video_id": video_id,
            "event_percentages": event_percentages,
            "analysis_report": analysis_report,
            "risk_level": risk_level,
            "effective_risk_percentage": effective_percentage
        }
        
        store_analysis_result(result)
        
        logger.info(f"✅ Successfully analyzed interview {interview_id}")
        return result
        
    except Exception as e:
        logger.exception(f"❌ Error analyzing interview {interview_id}: {str(e)}")
        raise


def main():
        """Entry point for CLI usage"""

        if len(sys.argv) < 2:
            logger.error("Usage: python -m ml.service.final_pipeline <video_path> [interview_id]")
            sys.exit(1)

        video_path = sys.argv[1]

        interview_id = 0
        if len(sys.argv) > 2:
            try:
                interview_id = int(sys.argv[2])
            except ValueError:
                logger.warning("Invalid interview_id, defaulting to 0")

        try:
            result = analyze_interview(video_path, interview_id)

            logger.info(f"Analysis complete: interview {interview_id}")

            print(json.dumps({
                "status": "success",
                "interview_id": interview_id,
                "risk_level": result["risk_level"],
                "effective_percentage": result["effective_risk_percentage"]
            }))

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")

            print(json.dumps({
                "status": "error",
                "interview_id": interview_id,
                "error": str(e)
            }))

            sys.exit(1)

 # ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()

