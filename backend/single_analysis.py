#!/usr/bin/env python3
"""
Single video analysis script for ML processing.
Usage: python single_analysis.py <video_path> <interview_id> <recording_id>
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ml.temporal_smoothing import analyze_single_video
from ml.process_behavior_from_csv import BehaviorRulesFromCSV, SuspiciousEventManager
from ml.service.event_percentage_calculator import convert_events_to_percentages
from ml.service.llm_client import generate_llm_analysis
from ml.service.risk_calculator import compute_effective_risk_percentage, classify_risk_level

def main():
    if len(sys.argv) != 4:
        print("Usage: python single_analysis.py <video_path> <interview_id> <recording_id>")
        sys.exit(1)

    video_path = sys.argv[1]
    interview_id = int(sys.argv[2])
    recording_id = int(sys.argv[3])

    # Set up directories
    logs_dir = project_root / "logs"
    events_dir = project_root / "events"
    logs_dir.mkdir(exist_ok=True)
    events_dir.mkdir(exist_ok=True)

    video_name = Path(video_path).name
    video_id = Path(video_path).stem

    # Step 1: Video → CSV + raw events
    _, video_duration, csv_path = analyze_single_video(video_path, output_folder=str(logs_dir))

    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    # Step 2: CSV → Behavior events
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

    event_json_path = events_dir / f"{video_id}_events.json"
    event_manager.save(str(event_json_path))

    # Step 3: Events → % exposure
    event_percentages = convert_events_to_percentages(
        event_json_path=str(event_json_path),
        video_duration=video_duration
    )

    # Step 4: Effective risk
    effective_percentage = compute_effective_risk_percentage(event_percentages)
    risk_level = classify_risk_level(effective_percentage)

    # Step 5: LLM analysis
    analysis_report = generate_llm_analysis(event_percentages, risk_level)

    # Extract events for frontend (suspicious gaze events)
    events = []
    if event_json_path.exists():
        with open(event_json_path, 'r') as f:
            event_data = json.load(f)
        for ev in event_data:
            if 'Gaze' in ev.get('event', '') and ev['event'] not in ['CENTER Gaze', 'WARMUP Gaze']:
                label = ev['event'].split()[0]  # e.g., "RIGHT" from "RIGHT Gaze"
                events.append({"timestamp": ev['start'], "label": label})

    # Return analysis in expected format
    analysis = {
        "recording_id": recording_id,
        "duration": video_duration,
        "events": events,
        "event_percentages": event_percentages,
        "risk_level": risk_level,
        "analysis_report": analysis_report
    }

    # Output the analysis JSON
    print(json.dumps(analysis))

if __name__ == "__main__":
    main()
