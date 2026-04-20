import os
from .extract_audio import extract_audio
from .transcribe_audio import transcribe
from .segment_answers import segment_qa_fixed_windows
from .scoring import score_segments
from .db_service import save_results
from app.core.database import SessionLocal
from app.models.analysis import InterviewAnalysis
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_video_path(interview_id):
    db = SessionLocal()
    try:
        interview = (
            db.query(InterviewAnalysis)
            .filter(
                InterviewAnalysis.interview_id == interview_id,
                InterviewAnalysis.video_path.isnot(None)
            )
            .first()
        )

        if not interview:
            raise Exception(f"❌ No video path found for interview {interview_id}")

        return interview.video_path

    finally:
        db.close()


def run_transcription_pipeline(video_path, interview_id):
    """Run the full pipeline using the provided video_path directly.

    Returns a dict with transcription text, segments, and scored segments
    so the API can return results to the frontend.
    """
    # 1. Extract audio
    audio_output_path = os.path.join(BASE_DIR, "uploads", f"audio_{interview_id}.wav")

    print("🎬 Video path:", video_path)

    if not os.path.exists(video_path):
        raise Exception(f"❌ Video file not found: {video_path}")

    audio_path = extract_audio(video_path, audio_output_path)

    if not audio_path:
        raise Exception("Audio extraction failed")

    # 2. Transcribe
    print("📝 Transcribing...")
    transcription = transcribe(audio_path)

    if not transcription:
        raise Exception("Transcription failed")

    # Build full transcript text
    full_text = " ".join(seg["text"] for seg in transcription)

    # 3. Segment
    print("✂️ Segmenting...")
    segments = segment_qa_fixed_windows(transcription)

    # 4. Score
    print("🧠 Scoring...")
    scored_segments = score_segments(segments)

    # 5. Save to DB
    print("💾 Saving results...")
    save_results(video_path, scored_segments, interview_id)

    print("✅ Transcription pipeline completed!")

    return {
        "transcription": transcription,
        "full_text": full_text,
        "segments": segments,
        "scored_segments": scored_segments,
    }

