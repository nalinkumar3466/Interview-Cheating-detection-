import os
import glob
import csv
import json

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
def main():

    video_files = glob.glob(os.path.join(UPLOADS_DIR, "*.*"))
    print(f"📂 Found {len(video_files)} video(s)")

    for video_path in video_files:
        video_name = os.path.basename(video_path)
        video_id = os.path.splitext(video_name)[0]

        try:
            print(f"\n🎥 Processing video: {video_name}")

            # --------------------------------------------------
            # STEP 1: VIDEO → CSV + RAW EVENTS
            # --------------------------------------------------
            _, video_duration, csv_path = analyze_single_video(video_path)

            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV not found: {csv_path}")

            # --------------------------------------------------
            # STEP 2: CSV → BEHAVIOR EVENTS
            # --------------------------------------------------
            event_manager = SuspiciousEventManager()
            fps = 30  # timestamps already in seconds

            behavior = BehaviorRulesFromCSV(
                fps=fps,
                event_manager=event_manager
            )

            with open(csv_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    gaze = row.get("Smooth_gaze", "CENTER")
                    t = float(row["Timestamp"])
                    blink_flag = row.get("Warmup_Frames", "NONE")

                    behavior.update(gaze, t, blink_flag)

            behavior.finalize()

            event_json_path = os.path.join(
                EVENTS_DIR, f"{video_id}_events.json"
            )
            event_manager.save(event_json_path)

            # --------------------------------------------------
            # STEP 3: EVENTS → % EXPOSURE
            # --------------------------------------------------
            event_percentages = convert_events_to_percentages(
                event_json_path=event_json_path,
                video_duration=video_duration
            )

            # --------------------------------------------------
            # STEP 4: EFFECTIVE RISK
            # --------------------------------------------------
            effective_percentage = compute_effective_risk_percentage(
                event_percentages
            )

            risk_level = classify_risk_level(effective_percentage)

            # --------------------------------------------------
            # STEP 5: LLM ANALYSIS (✅ FIXED CALL)
            # --------------------------------------------------
            analysis_report = generate_llm_analysis(
                event_percentages,
                risk_level
            )

            # --------------------------------------------------
            # STEP 6: STORE IN DATABASE
            # --------------------------------------------------
            store_analysis_result({
                "video_id": video_id,
                "event_percentages": json.dumps(event_percentages),
                "analysis_report": analysis_report,
                "risk_level": risk_level
            })

            print(
                f"✅ Stored analysis for {video_id} | "
                f"Risk: {risk_level} | "
                f"Exposure: {effective_percentage:.2f}%"
            )

        except Exception as e:
            print(f"❌ Error processing {video_name}: {e}")


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
