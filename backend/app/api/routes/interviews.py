from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
import logging
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db, engine, Base, SessionLocal
import time
import threading
import base64
from app.models.interview import Interview as InterviewModel
from app.schemas import InterviewCreate, Interview, InterviewOut, Question, QuestionPayload
from app.models.recording import Recording
from app.models.question import Question as QuestionModel
from app.models.analysis import InterviewAnalysis
from app.schemas_analysis import AnalysisOut
# canvas responses are stored separately when sketches are submitted
from app.models.canvas_response import CanvasResponse as CanvasResponseModel
import os
from sqlalchemy import insert
import uuid
from uuid import uuid4
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
@router.get("/{interview_id}/", response_model=InterviewOut)
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

        logger.info(f"ML completed for interview {interview_id}")

    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)

        analysis = db_session.query(InterviewAnalysis)\
            .filter(InterviewAnalysis.interview_id == interview_id)\
            .order_by(InterviewAnalysis.created_at.desc())\
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
    .order_by(Recording.created_at.desc())\
    .first()

    if not recording:
        raise HTTPException(400, "No recordings found")

    video_path = recording.file_path

    if not os.path.exists(video_path):
        raise HTTPException(400, f"Video not found: {video_path}")

    # Get/create analysis row
    analysis = db.query(InterviewAnalysis)\
    .filter(InterviewAnalysis.interview_id == payload.interview_id)\
    .order_by(InterviewAnalysis.created_at.desc())\
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
    print("Status:", analysis.status)
    result_obj = {
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
    print("Result:", result_obj)
    return result_obj
    
@router.get("/{interview_id}/analysis")
def get_analysis(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch analysis results from database.
    
    Returns analysis record with status, risk level, and event percentages.
    Returns None if no analysis exists (frontend handles gracefully).
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
    
    # Use safe default file_path to avoid NOT NULL constraint violation
    # This endpoint is for text answers without a file upload (e.g., auto-skip)
    file_path = f"text-answer-{interview_id}-{question_id}-{int(time.time())}"
    
    rec = Recording(interview_id=interview_id, question_id=question_id, file_path=file_path, answer_text=answer)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {'status': 'ok', 'recording_id': rec.id}

@router.post("/{interview_id}/sketch")
def submit_sketch(
    interview_id: int,
    question_id: int = Form(...),
    strokes: str = Form(...),
    image: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        strokes_data = json.loads(strokes)

        # Compute metadata
        stroke_count = len(strokes_data)

        first_time = strokes_data[0]["startedAt"]
        last_time = max(
            p["t"]
            for s in strokes_data
            for p in s["points"]
        )

        duration_ms = last_time - first_time

        # Save image file
        upload_dir = _uploads_dir()
          
        filename = f"sketch_{interview_id}_{question_id}_{int(time.time()*1000)}_{uuid4().hex[:8]}.png"
        save_path = os.path.join(upload_dir, filename)


        # image comes as base64 dataURL
        header, encoded = image.split(",", 1)
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(encoded))

        # Save in Recording table (reuse existing)
        rec = Recording(
            interview_id=interview_id,
            question_id=question_id,
            file_path=save_path,
            answer_text="canvas-sketch"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        # also persist as a proper canvas_response so it shows up
        try:
            canvas_resp = CanvasResponseModel(
                interview_id=interview_id,
                question_id=question_id,
                strokes_json=strokes_data,
                final_image_base64=image,
                duration_ms=duration_ms,
                stroke_count=stroke_count,
            )
            db.add(canvas_resp)
            db.commit()
            db.refresh(canvas_resp)
        except Exception as canvas_err:
            logger.exception("failed to create canvas_response from sketch: %s", canvas_err)

        return {
            "status": "ok",
            "recording_id": rec.id,
            "stroke_count": stroke_count,
            "duration_ms": duration_ms
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@router.post("/{interview_id}/answer")
def submit_answer(
    interview_id: int,
    question_id: int = Form(...),
    answer: str = Form(""),
    db: Session = Depends(get_db)
):
    # Use safe default file_path to avoid NOT NULL constraint violation
    # This endpoint is for text answers without a file upload (e.g., auto-skip)
    file_path = f"text-answer-{interview_id}-{question_id}-{int(time.time())}"
    
    rec = Recording(
        interview_id=interview_id,
        question_id=question_id,
        file_path="auto-skip",
        answer_text=answer
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {"status": "ok", "recording_id": rec.id}

@router.post("/{interview_id}/finish")
def finish_interview(
    interview_id: int,
    db: Session = Depends(get_db)
):
    interview = db.query(InterviewModel)\
        .filter(InterviewModel.id == interview_id)\
        .first()

    if not interview:
        raise HTTPException(404, "Interview not found")

    interview.status = "completed"
    db.commit()

    return {"status": "finished"}


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
       threading.Thread(
        target=_record_camera_task,
        args=(interview_id, duration_seconds, save_path, question_id, answer),
        daemon=True
    ).start()
   

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
        # Delete dependent records first - ADD THIS LINE
        db.query(CanvasResponseModel).filter(
            CanvasResponseModel.interview_id == interview_id
        ).delete(synchronize_session=False)
        
        # Delete other dependent records
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


# -------------------- AI Transcription & Scoring Pipeline --------------------

@router.post("/{interview_id}/transcribe")
def trigger_transcription_pipeline(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Trigger the AI scoring pipeline for a given interview.
    Extracts audio from the video recording, transcribes it,
    segments into Q&A pairs, scores each segment, and saves to DB.
    Returns the full transcription and scored segments.
    """
    # Check interview exists
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id
    ).first()
    if not interview:
        raise HTTPException(404, "Interview not found")

    # Get the latest recording
    recording = db.query(Recording).filter(
        Recording.interview_id == interview_id
    ).order_by(Recording.created_at.desc()).first()

    if not recording:
        raise HTTPException(400, "No recordings found for this interview")

    video_path = recording.file_path
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(400, f"Video file not found at: {video_path}")

    try:
        from ai_scoring_pipeline.pipeline import run_transcription_pipeline
        result = run_transcription_pipeline(video_path, interview_id)

        return {
            "status": "completed",
            "full_text": result.get("full_text", ""),
            "transcription": result.get("transcription", []),
            "scored_segments": result.get("scored_segments", []),
        }

    except Exception as e:
        logger.exception("Transcription pipeline failed for interview %s: %s", interview_id, e)
        raise HTTPException(500, f"Transcription pipeline failed: {str(e)}")


@router.get("/{interview_id}/transcription")
def get_transcription(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch saved transcription & scoring results from the DB.
    Returns all interview_analysis rows that have question/answer data
    (populated by the ai_scoring_pipeline).
    """
    rows = db.query(InterviewAnalysis).filter(
        InterviewAnalysis.interview_id == interview_id,
        InterviewAnalysis.question.isnot(None),
    ).order_by(InterviewAnalysis.created_at.asc()).all()

    if not rows:
        return {"status": "not_found", "scored_segments": []}

    scored_segments = []
    for row in rows:
        scored_segments.append({
            "question": row.question or "",
            "answer": row.answer or "",
            "final_score": row.score,
            "id": row.id,
        })

    return {
        "status": "completed",
        "scored_segments": scored_segments,
    }


# -------------------- PDF Report Endpoints --------------------

from fastapi.responses import StreamingResponse
from io import BytesIO

def _safe_text(text):
    """Sanitize text for fpdf2 – replace characters that latin-1 cannot encode."""
    if not text:
        return ""
    # Replace common problematic characters
    return text.encode('latin-1', errors='replace').decode('latin-1')


@router.get("/{interview_id}/report/gaze-pdf")
def download_gaze_report_pdf(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate and return a downloadable PDF report of the gaze detection analysis
    for the given interview. Includes risk level, gaze distribution percentages,
    AI analysis report, and suspicious events.
    """
    from fpdf import FPDF

    # Fetch interview
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id
    ).first()
    if not interview:
        raise HTTPException(404, "Interview not found")

    # Fetch analysis
    analysis = db.query(InterviewAnalysis).filter(
        InterviewAnalysis.interview_id == interview_id
    ).first()
    if not analysis:
        raise HTTPException(404, "No analysis data available for this interview. Run analysis first.")

    try:
        event_data = json.loads(analysis.event_percentages or "[]")
    except Exception:
        event_data = []

    # Build PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, _safe_text("Gaze Detection Analysis Report"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Interview Info
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(f"Interview: {interview.title or 'N/A'}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Candidate: {interview.candidate_name or 'N/A'}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Email: {interview.candidate_email or 'N/A'}"), new_x="LMARGIN", new_y="NEXT")
    scheduled = interview.scheduled_at.strftime("%Y-%m-%d %H:%M UTC") if interview.scheduled_at else "N/A"
    pdf.cell(0, 7, _safe_text(f"Scheduled At: {scheduled}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Separator
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Risk Level
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Risk Assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    risk = analysis.risk_level or "Not determined"
    pdf.cell(0, 8, _safe_text(f"Risk Level: {risk.upper()}"), new_x="LMARGIN", new_y="NEXT")
    if analysis.effective_risk_percentage is not None:
        pdf.cell(0, 8, _safe_text(f"Effective Risk Percentage: {analysis.effective_risk_percentage:.1f}%"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Gaze Distribution
    if event_data:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Gaze Distribution", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)

        # Table header
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(100, 8, "Event Name", border=1, fill=True)
        pdf.cell(50, 8, "Percentage (%)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        for item in event_data:
            name = item.get("event_name", "Unknown")
            pct = item.get("percentage_in_video", 0)
            pdf.cell(100, 7, _safe_text(str(name)), border=1)
            pdf.cell(50, 7, _safe_text(f"{pct}%"), border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

    # AI Analysis Report
    if analysis.analysis_report:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "AI Analysis Report", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _safe_text(analysis.analysis_report))
        pdf.ln(6)

    # Suspicious Events
    events_list = [
        {"label": e.get("event_name"), "timestamp": round(e.get("percentage_in_video", 0), 2)}
        for e in event_data
    ]
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _safe_text(f"Suspicious Events ({len(events_list)} detected)"), new_x="LMARGIN", new_y="NEXT")

    if events_list:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(15, 8, "#", border=1, fill=True)
        pdf.cell(100, 8, "Event Label", border=1, fill=True)
        pdf.cell(40, 8, "Timestamp (s)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        for i, ev in enumerate(events_list):
            pdf.cell(15, 7, str(i + 1), border=1)
            pdf.cell(100, 7, _safe_text(str(ev["label"] or "N/A")), border=1)
            pdf.cell(40, 7, str(ev["timestamp"]), border=1, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, "No suspicious events detected.", new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Generated by BerriBot Interview Assessment Platform", new_x="LMARGIN", new_y="NEXT", align="C")

    # Output as bytes
    pdf_bytes = pdf.output()
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)

    filename = f"gaze_report_interview_{interview_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{interview_id}/report/transcription-pdf")
def download_transcription_report_pdf(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate and return a downloadable PDF report of the transcription
    and scored Q&A segments for the given interview.
    """
    from fpdf import FPDF

    # Fetch interview
    interview = db.query(InterviewModel).filter(
        InterviewModel.id == interview_id
    ).first()
    if not interview:
        raise HTTPException(404, "Interview not found")

    # Fetch transcription segments (scored)
    rows = db.query(InterviewAnalysis).filter(
        InterviewAnalysis.interview_id == interview_id,
        InterviewAnalysis.question.isnot(None),
    ).order_by(InterviewAnalysis.created_at.asc()).all()

    if not rows:
        raise HTTPException(404, "No transcription data available for this interview. Run transcription first.")

    # Build PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, _safe_text("Interview Transcription Report"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Interview Info
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(f"Interview: {interview.title or 'N/A'}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Candidate: {interview.candidate_name or 'N/A'}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Email: {interview.candidate_email or 'N/A'}"), new_x="LMARGIN", new_y="NEXT")
    scheduled = interview.scheduled_at.strftime("%Y-%m-%d %H:%M UTC") if interview.scheduled_at else "N/A"
    pdf.cell(0, 7, _safe_text(f"Scheduled At: {scheduled}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _safe_text(f"Total Segments: {len(rows)}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Separator
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Full Transcription (combine all answers)
    full_text = " ".join((row.answer or "") for row in rows if row.answer)
    if full_text.strip():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Full Transcription", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _safe_text(full_text.strip()))
        pdf.ln(6)

        # Page break before segments
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

    # Scored Q&A Segments
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Scored Q&A Segments", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for i, row in enumerate(rows):
        # Segment header
        pdf.set_font("Helvetica", "B", 12)
        score_text = f" | Score: {row.score:.1f}/10" if row.score is not None else ""
        pdf.cell(0, 9, _safe_text(f"Segment {i + 1}{score_text}"), new_x="LMARGIN", new_y="NEXT")

        # Question
        if row.question:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Question:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _safe_text(row.question))
            pdf.ln(2)

        # Answer
        if row.answer:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Answer:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _safe_text(row.answer))
            pdf.ln(2)

        # Score
        if row.score is not None:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(25, 7, "Score: ")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, _safe_text(f"{row.score:.1f} / 10"), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(4)
        # Segment separator
        pdf.set_draw_color(230, 230, 230)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

    # Summary table
    scores = [row.score for row in rows if row.score is not None]
    if scores:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Score Summary", new_x="LMARGIN", new_y="NEXT")

        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, _safe_text(f"Average Score: {avg_score:.1f} / 10"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, _safe_text(f"Highest Score: {max_score:.1f} / 10"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, _safe_text(f"Lowest Score: {min_score:.1f} / 10"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, _safe_text(f"Total Segments Scored: {len(scores)}"), new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Generated by BerriBot Interview Assessment Platform", new_x="LMARGIN", new_y="NEXT", align="C")

    # Output as bytes
    pdf_bytes = pdf.output()
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)

    filename = f"transcription_report_interview_{interview_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
