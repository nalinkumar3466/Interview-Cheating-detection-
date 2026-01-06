import json
import os
from collections import defaultdict

SUSPICIOUS_EVENTS = {
    "Long Gaze Away",
    "Frequent Distraction",
    "Reading Pattern",
    "Frequent Downward Gaze"
}

def convert_events_to_percentages(event_json_path, video_duration):
    """
    Convert event timestamps into percentage of total video duration.
    """

    # ---- FIX: resolve absolute path safely ----
    if not os.path.isabs(event_json_path):
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )
        event_json_path = os.path.join(project_root, event_json_path)

    if not os.path.exists(event_json_path):
        raise FileNotFoundError(f"Event file not found: {event_json_path}")

    with open(event_json_path, "r") as f:
        events = json.load(f)

    event_durations = defaultdict(float)

    for e in events:
        event_name = e.get("event")
        if event_name not in SUSPICIOUS_EVENTS:
            continue

        start = e.get("start", 0)
        end = e.get("end", 0)
        duration = max(0, end - start)
        
        event_durations[event_name] += duration

    percentages = []

    for event_name, total_time in event_durations.items():
        percentage = (total_time / video_duration) * 100
        percentages.append({
            "event_name": event_name,
            "percentage_in_video": round(percentage, 2)
        })

    return percentages
