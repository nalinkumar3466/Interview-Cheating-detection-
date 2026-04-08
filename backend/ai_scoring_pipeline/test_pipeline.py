from ai_scoring_pipeline.pipeline import run_pipeline

print("🚀 Testing pipeline...")

results = run_pipeline(
    video_path=r"C:\Users\HP\PycharmProjects\Interview-Cheating-detection--1\backend\uploads\interview_21_0_rec_1775575143858.webm",
    interview_id=23
)


print("\n🎯 Final Results:")
for r in results:
    print(r)

