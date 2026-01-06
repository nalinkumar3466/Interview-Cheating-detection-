from ml.service.analyzer import InterviewAnalysisService

# ⚠️ Use a short test video you already processed before
VIDEO_PATH = "ml/samples/down.mp4"

service = InterviewAnalysisService()
result = service.analyze_video(VIDEO_PATH)

print("\n=== FINAL ML OUTPUT ===")
print(result)
