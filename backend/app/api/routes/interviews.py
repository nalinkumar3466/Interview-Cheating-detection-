from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db, engine, Base, SessionLocal
import time
import threading
from app.models.interview import Interview as InterviewModel
from app.schemas import InterviewCreate, Interview, InterviewOut, Question, QuestionPayload
from app.models.recording import Recording
from app.models.question import Question as QuestionModel
from app.models.analysis import InterviewAnalysis
from app.schemas_analysis import AnalysisOut
import os
from sqlalchemy import insert
import uuid
from datetime import datetime, timezone, timedelta
import os
import sys
import subprocess
import json
import smtplib
from email.message import EmailMessage
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

router = APIRouter(prefix="/interviews", tags=["interviews"]) 
logger = logging.getLogger(__name__)

def _send_candidate_email(interview_id: int, token: str, candidate_email: str, base_url: str):
    try:
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        from_addr = os.getenv('FROM_EMAIL', smtp_user)
        if not smtp_host or not smtp_user or not smtp_pass:
            logger.info('SMTP not configured; skipping candidate email send')
            return

        link = f"{base_url.rstrip('/')}/candidate/interview/{token}"
        msg = EmailMessage()
        msg['Subject'] = 'Your interview link'
        msg['From'] = from_addr
        msg['To'] = candidate_email
        msg.set_content(f"Hello,\n\nPlease join your interview using the link below:\n\n{link}\n\nThis link is valid for the scheduled time.\n\nGood luck.")

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        logger.info('Candidate email sent to %s', candidate_email)
    except Exception as e:
        logger.exception('Failed to send candidate email: %s', e)


@router.post("/", response_model=InterviewOut, status_code=201)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    logger.info('Received create_interview payload: %s', payload.json())
    # Normalize scheduled_at to UTC
    sched: datetime = payload.scheduled_at
    if sched.tzinfo is None:
        # if timezone provided, use it; otherwise assume UTC
        if getattr(payload, 'timezone', None) and ZoneInfo is not None:
            try:
                tz = ZoneInfo(payload.timezone)
                sched = sched.replace(tzinfo=tz)
            except Exception:
                # fallback: treat as UTC
                sched = sched.replace(tzinfo=timezone.utc)
        else:
            sched = sched.replace(tzinfo=timezone.utc)
    sched_utc = sched.astimezone(timezone.utc)

    # token generation and TTL
    token = uuid.uuid4().hex
    ttl_minutes = getattr(payload, 'token_ttl_minutes', None) or (payload.duration_minutes * 4)
    token_expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

    new_interview = InterviewModel(
        title=payload.title,
        candidate_name=payload.candidate_name,
        candidate_email=str(payload.candidate_email),
        scheduled_at=sched_utc,
        duration_minutes=payload.duration_minutes,
        timezone=payload.timezone,
        instructions=payload.instructions,
        token=token,
        token_expires_at=token_expires,
        status='scheduled'
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    # create ordered questions
    for q in sorted(payload.questions, key=lambda x: x.order):
        qm = QuestionModel(interview_id=new_interview.id, order=q.order, text=q.text, examples=q.examples, type=q.type)
        db.add(qm)
    db.commit()
    # schedule sending candidate email asynchronously if SMTP configured
    try:
        base_url = os.getenv('FRONTEND_BASE', 'http://localhost:5173')
        if background_tasks is not None:
            background_tasks.add_task(_send_candidate_email, new_interview.id, new_interview.token, new_interview.candidate_email, base_url)
        else:
            # best-effort: fire-and-forget
            try:
                _send_candidate_email(new_interview.id, new_interview.token, new_interview.candidate_email, base_url)
            except Exception:
                pass
    except Exception:
        logger.exception('Error scheduling candidate email')

    return new_interview


@router.post("/{interview_id}/complete")
def complete_interview(interview_id: int, file: UploadFile = File(...), answer: str = Form(None), question_id: int | None = Form(None), db: Session = Depends(get_db)):
    # save file to disk
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', '..', 'uploads')
    # simplify path: put uploads in backend/uploads under project root
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    upload_dir = os.path.join(base, 'backend', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"interview_{interview_id}_{int(os.times()[4])}_{file.filename}"
    save_path = os.path.join(upload_dir, filename)
    with open(save_path, 'wb') as f:
        f.write(file.file.read())

    rec = Recording(interview_id=interview_id, question_id=question_id, file_path=save_path, answer_text=answer)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"status":"ok","recording_id": rec.id, "file_path": save_path}

@router.get("/", response_model=List[InterviewOut])
def list_interviews(db: Session = Depends(get_db)):
    items = db.query(InterviewModel).all()
    return items


@router.get("/{interview_id}/questions", response_model=List[Question])
def list_questions(interview_id: int, db: Session = Depends(get_db)):
    items = db.query(QuestionModel).filter(QuestionModel.interview_id == interview_id).all()
    return items


@router.post("/{interview_id}/questions", response_model=Question, status_code=201)
def create_question(interview_id: int, payload: QuestionPayload, db: Session = Depends(get_db)):
    q = QuestionModel(interview_id=interview_id, order=payload.order, text=payload.text, examples=payload.examples, type=payload.type)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    item = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Interview not found')
    return item


def _record_camera_task(interview_id: int, duration: float, save_path: str, question_id: int | None = None, answer_text: str | None = None):
    """Background task: record from the default camera and save to save_path, then create a Recording DB entry."""
    try:
        import cv2
    except Exception as e:
        logger.exception("opencv not available: %s", e)
        return

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Camera not available or cannot be opened")
            return

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        fps = 10.0
        out = cv2.VideoWriter(save_path, fourcc, fps, (w, h))

        start_time = time.time()
        while (time.time() - start_time) < float(duration):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        try:
            cap.release()
        except Exception:
            pass
        try:
            out.release()
        except Exception:
            pass
    except Exception as e:
        logger.exception("Error during camera recording: %s", e)

    # create a DB entry for the saved file
    try:
        db = SessionLocal()
        rec = Recording(interview_id=interview_id, question_id=question_id, file_path=save_path, answer_text=answer_text)
        db.add(rec)
        db.commit()
        db.refresh(rec)
    except Exception:
        logger.exception("Failed to save recording metadata to DB")
    finally:
        try:
            db.close()
        except Exception:
            pass


def _uploads_dir():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    upload_dir = os.path.join(base, 'backend', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _run_ml_pipeline(interview_id: int, video_path: str):
    db_session = SessionLocal()
    try:
        logger.info(f"Starting ML pipeline for interview {interview_id}")

        # Mark processing
        analysis = db_session.query(InterviewAnalysis)\
            .filter(InterviewAnalysis.interview_id == interview_id)\
            .first()

        if analysis:
            analysis.status = "processing"
            db_session.commit()

        # Prepare env
        env = os.environ.copy()

        PROJECT_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        )

        env["PYTHONPATH"] = os.path.join(PROJECT_ROOT, "backend")

        cmd = [
            sys.executable,
            "-m",
            "ml.service.final_pipeline",
            video_path,
            str(interview_id)
        ]

        logger.info(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=PROJECT_ROOT,
            env=env,
            check=True
        )

        logger.info(result.stdout)

        # Reload DB result
        analysis = db_session.query(InterviewAnalysis)\
            .filter(InterviewAnalysis.interview_id == interview_id)\
            .order_by(InterviewAnalysis.created_at.desc())\
            .first()

        if analysis:
            analysis.status = "completed"
            db_session.commit()

        logger.info(f"ML completed for interview {interview_id}")

    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)

        analysis = db_session.query(InterviewAnalysis)\
            .filter(InterviewAnalysis.interview_id == interview_id)\
            .first()

        if analysis:
            analysis.status = "failed"
            analysis.error_message = e.stderr
            db_session.commit()

    except Exception as e:
        logger.exception(e)

        analysis = db_session.query(InterviewAnalysis)\
            .filter(InterviewAnalysis.interview_id == interview_id)\
            .first()

        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db_session.commit()

    finally:
        db_session.close()

# -------------------- Analysis endpoints --------------------

class AnalysisPayload(BaseModel):
    interview_id: int

@router.post("/analyze")
def trigger_analysis(
    payload: AnalysisPayload,
    db: Session = Depends(get_db)
):

    # Check interview
    interview = db.query(InterviewModel)\
        .filter(InterviewModel.id == payload.interview_id)\
        .first()

    if not interview:
        raise HTTPException(404, "Interview not found")

    # Get recording
    recording = db.query(Recording)\
        .filter(Recording.interview_id == payload.interview_id)\
        .first()

    if not recording:
        raise HTTPException(400, "No recordings found")

    video_path = recording.file_path

    if not os.path.exists(video_path):
        raise HTTPException(400, f"Video not found: {video_path}")

    # Get/create analysis row
    analysis = db.query(InterviewAnalysis)\
        .filter(InterviewAnalysis.interview_id == payload.interview_id)\
        .first()

    if not analysis:
        analysis = InterviewAnalysis(
            interview_id=payload.interview_id,
            status="pending"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

    # RUN ML (blocking)
    _run_ml_pipeline(payload.interview_id, video_path)

    # Reload result
    analysis = db.query(InterviewAnalysis)\
        .filter(InterviewAnalysis.interview_id == payload.interview_id)\
        .order_by(InterviewAnalysis.created_at.desc())\
        .first()

    if not analysis:
        raise HTTPException(500, "Analysis failed")

    try:
        events = json.loads(analysis.event_percentages or "[]")
    except Exception:
        events = []

    return {
        "status": analysis.status,
        "risk_level": analysis.risk_level,
        "event_percentages": events,
        "analysis_report": analysis.analysis_report,
        "events": [
            {
                "label": e.get("event_name"),
                "timestamp": round(e.get("percentage_in_video", 0), 2)
            }
            for e in events
        ]
    }
@router.get("/{interview_id}/analysis", response_model=AnalysisOut)
def get_analysis(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch analysis results from database.
    
    Returns analysis record with status, risk level, and event percentages.
    """
    analysis = db.query(InterviewAnalysis).filter(
        InterviewAnalysis.interview_id == interview_id
    ).first()

    if not analysis:
        return None

    try:
        event_data = json.loads(analysis.event_percentages or "[]")
    except Exception:
        event_data = []

    return {
        "status": analysis.status,
        "risk_level": analysis.risk_level,
        "event_percentages": event_data,
        "analysis_report": analysis.analysis_report,
        "events": [
            {
                "label": e.get("event_name"),
                "timestamp": round(e.get("percentage_in_video", 0), 2)
            }
            for e in event_data
        ]
    }


@router.post("/{interview_id}/complete-with-analysis")
def complete_interview_with_analysis(
    interview_id: int,
    file: UploadFile = File(...),
    answer: str = Form(None),
    question_id: int | None = Form(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Complete interview (save recording) and automatically trigger ML analysis.
    
    This is a convenience endpoint that combines recording upload with analysis.
    """
    try:
        # Save recording
        upload_dir = _uploads_dir()
        filename = f"interview_{interview_id}_{int(time.time())}_{file.filename}"
        save_path = os.path.join(upload_dir, filename)
        
        with open(save_path, 'wb') as f:
            f.write(file.file.read())
        
        rec = Recording(
            interview_id=interview_id,
            question_id=question_id,
            file_path=save_path,
            answer_text=answer
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        
        logger.info(f"Recording saved: {save_path}")
        
        # Create analysis record
        analysis = db.query(InterviewAnalysis).filter(
            InterviewAnalysis.interview_id == interview_id
        ).first()
        
        if not analysis:
            analysis = InterviewAnalysis(
                interview_id=interview_id,
                status='pending'
            )
            db.add(analysis)
            db.commit()
        
        # Trigger background analysis task
        if background_tasks:
            background_tasks.add_task(
                _run_ml_pipeline,
                interview_id,
                save_path,
                SessionLocal()
            )
        
        return {
            "status": "ok",
            "recording_id": rec.id,
            "file_path": save_path,
            "analysis_queued": True,
            "analysis_id": analysis.id
        }
        
    except Exception as e:
        logger.exception(f"Error in complete_interview_with_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Candidate endpoints (token-limited) --------------------
from app.models.candidatelog import CandidateLog
from fastapi import Header, Body


def _validate_token(db: Session, token: str, interview_id: int | None = None):
    if not token:
        return False, None
    now = datetime.now(timezone.utc)
    q = db.query(InterviewModel).filter(InterviewModel.token == token).first()
    if not q:
        return False, None
    # normalize token_expires_at to timezone-aware for safe comparison
    exp = q.token_expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp and exp < now:
        return False, None
    if interview_id is not None and q.id != int(interview_id):
        return False, None
    return True, q


@router.get('/candidate/validate/{token}')
def candidate_validate(token: str, db: Session = Depends(get_db)):
    valid, interview = _validate_token(db, token)
    if not valid:
        return {'valid': False}
    return {'valid': True, 'interview_id': interview.id}


@router.get('/candidate/interviews/{interview_id}/questions')
def candidate_questions(interview_id: int, x_candidate_token: str | None = Header(None), db: Session = Depends(get_db)):
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    items = db.query(QuestionModel).filter(QuestionModel.interview_id == interview_id).order_by(QuestionModel.order).all()
    # return minimal question info
    results = []
    for q in items:
        results.append({'id': q.id, 'interview_id': q.interview_id, 'order': q.order, 'text': q.text, 'examples': q.examples, 'type': q.type})
    return results


@router.post('/candidate/interviews/{interview_id}/answer')
def candidate_answer(interview_id: int, question_id: int | None = Form(None), answer: str | None = Form(None), x_candidate_token: str | None = Header(None), db: Session = Depends(get_db)):
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    rec = Recording(interview_id=interview_id, question_id=question_id, answer_text=answer)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {'status': 'ok', 'recording_id': rec.id}


@router.post('/candidate/interviews/{interview_id}/complete')
def candidate_complete(interview_id: int, file: UploadFile = File(...), answer: str = Form(None), question_id: int | None = Form(None), x_candidate_token: str | None = Header(None), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    # reuse file saving logic
    upload_dir = _uploads_dir()
    filename = f"candidate_interview_{interview_id}_{int(time.time())}_{file.filename}"
    save_path = os.path.join(upload_dir, filename)
    with open(save_path, 'wb') as f:
        f.write(file.file.read())
    rec = Recording(interview_id=interview_id, question_id=question_id, file_path=save_path, answer_text=answer)
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Trigger automatic analysis in background
    if background_tasks is not None:
        background_tasks.add_task(run_analysis_background, interview_id)

    return {'status': 'ok', 'recording_id': rec.id, 'file_path': save_path}


@router.post('/candidate/log')
def candidate_log(payload: dict = Body(...), db: Session = Depends(get_db)):
    # payload should include token, interview_id, event, ts, detail
    token = payload.get('token')
    interview_id = payload.get('interview_id')
    event = payload.get('event')
    detail = payload.get('detail')
    # optional validation: ensure token maps to interview
    try:
        ok, _ = _validate_token(db, token, interview_id if interview_id is not None else None)
    except Exception:
        ok = False
    # still log even if invalid (for audit)
    cl = CandidateLog(interview_id=interview_id, token=token, event=event or 'unknown', detail=str(detail))
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return {'status': 'logged', 'id': cl.id, 'valid_token': ok}



def run_ml_analysis(video_path: str, interview_id: int, recording_id: int):
    """Run the advanced ML analysis pipeline on a single video using subprocess."""
    import subprocess
    import json
    from pathlib import Path

    script_path = Path(__file__).parent / 'single_analysis.py'
    result = subprocess.run([
        sys.executable, str(script_path),
        video_path, str(interview_id), str(recording_id)
    ], cwd=Path(__file__).parent.parent, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Analysis failed: {result.stderr}")

    # Parse the JSON output
    analysis = json.loads(result.stdout.strip())
    return analysis


def run_analysis_background(interview_id: int):
    """Background task to run analysis after interview completion."""
    try:
        db = SessionLocal()
        rec = db.query(Recording).filter(Recording.interview_id == interview_id).order_by(Recording.created_at.desc()).first()
        if rec:
            analysis = run_ml_analysis(rec.file_path, interview_id, rec.id)
            upload_dir = _uploads_dir()
            analysis_file = os.path.join(upload_dir, f"analysis_{interview_id}.json")
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f)
            logger.info(f"Background analysis completed for interview {interview_id}")
        db.close()
    except Exception as e:
        logger.exception(f"Background analysis failed for interview {interview_id}: {e}")


@router.get("/{interview_id}/recordings")
def list_recordings(interview_id: int, db: Session = Depends(get_db)):
    items = db.query(Recording).filter(Recording.interview_id == interview_id).order_by(Recording.created_at.desc()).all()
    upload_dir = _uploads_dir()
    results = []
    for r in items:
        filename = os.path.basename(r.file_path)
        file_url = f"/uploads/{filename}"
        results.append({
            "id": r.id,
            "file_path": r.file_path,
            "file_url": file_url,
            "answer_text": r.answer_text,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return results


@router.post("/{interview_id}/record_camera")
def record_camera(interview_id: int, duration_seconds: int = Form(10), filename: str | None = Form(None), question_id: int | None = Form(None), answer: str | None = Form(None), background_tasks: BackgroundTasks = None):
    """Start a camera-only recording on the server for a given duration (seconds).

    The recording runs in the background and is saved to the backend/uploads folder.
    Returns the target file path (on the server) immediately.
    """
    upload_dir = _uploads_dir()
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = filename or f"camera_{int(time.time())}.mp4"
    save_path = os.path.join(upload_dir, f"interview_{interview_id}_{safe_name}")

    # schedule background recording
    if background_tasks is not None:
        background_tasks.add_task(_record_camera_task, interview_id, duration_seconds, save_path, question_id, answer)
    else:
        # fallback: run in a thread (non-blocking)
        t = threading.Thread(target=_record_camera_task, args=(interview_id, duration_seconds, save_path, question_id, answer), daemon=True)
        t.start()

    return {"status": "recording_started", "file_path": save_path, "message": "Recording started in background on the server camera."}


@router.delete("/{interview_id}")
def delete_interview(interview_id: int, db: Session = Depends(get_db)):
    # delete recordings (and files) + questions + analysis + logs + interview
    item = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Interview not found')

    # delete recording files
    recs = db.query(Recording).filter(Recording.interview_id == interview_id).all()
    for r in recs:
        try:
            if r.file_path and os.path.exists(r.file_path):
                os.remove(r.file_path)
        except Exception:
            pass

    # remove DB rows (delete in correct order to handle foreign keys)
    try:
        # Delete dependent records first
        db.query(CandidateLog).filter(CandidateLog.interview_id == interview_id).delete(synchronize_session=False)
        db.query(InterviewAnalysis).filter(InterviewAnalysis.interview_id == interview_id).delete(synchronize_session=False)
        db.query(Recording).filter(Recording.interview_id == interview_id).delete(synchronize_session=False)
        db.query(QuestionModel).filter(QuestionModel.interview_id == interview_id).delete(synchronize_session=False)
        # Finally delete the interview itself
        db.delete(item)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception('Failed to delete interview: %s', e)
        raise HTTPException(status_code=500, detail='Failed to delete interview')

    return {"status": "deleted"}
