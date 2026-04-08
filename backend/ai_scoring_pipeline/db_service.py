from app.models.analysis import InterviewAnalysis
from app.core.database import SessionLocal


def save_results(video_path, segments, interview_id):
    db = SessionLocal()

    try:
        print("📦 Saving to DB...")

        for seg in segments:

            print("➡️ Inserting:", seg)   # 👈 DEBUG

            record = InterviewAnalysis(
                interview_id=interview_id,
                video_path=video_path,
                question=seg.get("question"),
                answer=seg.get("answer"),
                score=seg.get("final_score")
            )
            db.add(record)

        db.commit()
        print("✅ Data committed successfully!")

    except Exception as e:
        db.rollback()
        print("❌ ERROR:", e)

    finally:
        db.close()
        print("🔒 DB connection closed")


