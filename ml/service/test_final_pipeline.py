from ml.service.analyzer import InterviewAnalysisService
from ml.service.analyzer import store_analysis_result
import os

def main():
    service = InterviewAnalysisService()

    # 1️⃣ Run analysis from event JSON
    result = service.analyze_from_event_json(
        video_id="interview_002",
        event_json_path="ml/events/interviewsample1_events.json",
        video_duration=30.0
    )

    # 2️⃣ Store result in DB
    store_analysis_result(result)

    print("✅ Final analysis stored successfully")
    print(result)

if __name__ == "__main__":
    main()
