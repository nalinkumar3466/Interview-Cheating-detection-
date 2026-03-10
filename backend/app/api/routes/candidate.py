from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.interview import Interview as InterviewModel
from app.models.question import Question as QuestionModel
from app.models.recording import Recording
from app.models.candidatelog import CandidateLog
from app.models.canvas_response import CanvasResponse as CanvasResponseModel
import os, time, json
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/candidate", tags=["candidate"])


def _uploads_dir():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    upload_dir = os.path.join(base, 'backend', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _validate_token(db: Session, token: str, interview_id: int | None = None):
    if not token:
        return False, None
    now = datetime.now(timezone.utc)
    q = db.query(InterviewModel).filter(InterviewModel.token == token).first()
    if not q:
        return False, None
    exp = q.token_expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp and exp < now:
        return False, None
    if interview_id is not None and q.id != int(interview_id):
        return False, None
    return True, q


@router.get('/validate/{token}')
def validate(token: str, db: Session = Depends(get_db)):
    ok, interview = _validate_token(db, token)
    if not ok:
        return {'valid': False}
    return {'valid': True, 'interview_id': interview.id}


@router.get('/interviews/{interview_id}/questions')
def questions(interview_id: int, x_candidate_token: str | None = Header(None), db: Session = Depends(get_db)):
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    items = db.query(QuestionModel).filter(QuestionModel.interview_id == interview_id).order_by(QuestionModel.order).all()
    return [{'id': q.id, 'interview_id': q.interview_id, 'order': q.order, 'text': q.text, 'examples': q.examples, 'type': q.type} for q in items]


@router.post('/interviews/{interview_id}/answer')
def answer(interview_id: int, question_id: int | None = Form(None), answer: str | None = Form(None), x_candidate_token: str | None = Header(None), db: Session = Depends(get_db)):
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    rec = Recording(interview_id=interview_id, question_id=question_id, answer_text=answer)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {'status': 'ok', 'recording_id': rec.id}


@router.post('/interviews/{interview_id}/complete')
def complete(interview_id: int, file: UploadFile = File(...), answer: str = Form(None), question_id: int | None = Form(None), x_candidate_token: str | None = Header(None), db: Session = Depends(get_db)):
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    upload_dir = _uploads_dir()
    filename = f"candidate_interview_{interview_id}_{int(time.time())}_{file.filename}"
    save_path = os.path.join(upload_dir, filename)
    with open(save_path, 'wb') as f:
        f.write(file.file.read())
    rec = Recording(interview_id=interview_id, question_id=question_id, file_path=save_path, answer_text=answer)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {'status': 'ok', 'recording_id': rec.id, 'file_path': save_path}


@router.post('/log')
def log(payload: dict = Body(...), db: Session = Depends(get_db)):
    token = payload.get('token')
    interview_id = payload.get('interview_id')
    event = payload.get('event')
    detail = payload.get('detail')
    try:
        ok, _ = _validate_token(db, token, interview_id if interview_id is not None else None)
    except Exception:
        ok = False
    cl = CandidateLog(interview_id=interview_id, token=token, event=event or 'unknown', detail=str(detail))
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return {'status': 'logged', 'id': cl.id, 'valid_token': ok}

# Canvas Drawing Schema for candidate submission
class CandidateCanvasSubmission(BaseModel):
    question_id: int
    strokes: List[dict]
    final_image: str
    duration: Optional[int] = None
    stroke_count: Optional[int] = None


def _compute_canvas_metadata(strokes_json):
    """
    Compute canvas session metadata:
    - stroke_count: total number of strokes
    - duration: time from first to last point (seconds)
    """
    if not strokes_json:
        return {"strokeCount": 0, "duration": 0}

    stroke_count = len(strokes_json)
    
    # Find min and max timestamps
    min_time = float('inf')
    max_time = 0
    
    for stroke in strokes_json:
        if isinstance(stroke, dict) and 'points' in stroke:
            points = stroke['points']
            if points:
                for point in points:
                    if isinstance(point, dict) and 't' in point:
                        t = point['t']
                        if t < min_time:
                            min_time = t
                        if t > max_time:
                            max_time = t
    
    # Duration in seconds
    duration = 0
    if min_time != float('inf') and max_time != 0:
        duration = (max_time - min_time) / 1000.0
    
    return {
        "strokeCount": stroke_count,
        "duration": max(0, int(duration)),
        "submittedAt": datetime.now(timezone.utc).isoformat()
    }


@router.post('/interviews/{interview_id}/sketch')
def submit_sketch(
    interview_id: int,
    question_id: int = Form(...),
    strokes: str = Form(...),
    image: str = Form(...),
    x_candidate_token: str | None = Header(None),
    db: Session = Depends(get_db)
):
    """
    Candidate submission of canvas sketch (form data version).
    Validates token and stores canvas response with computed metadata.
    """
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    
    # Parse strokes JSON
    try:
        strokes_json = json.loads(strokes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid strokes JSON")
    
        # Verify question exists and is canvas_drawing type
    question = db.query(QuestionModel).filter(QuestionModel.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail='Question not found')
    qtype = (question.type or '').lower()
    if qtype not in ("canvas_drawing", "sketch"):
        raise HTTPException(status_code=400, detail='Question is not a canvas_drawing type')

    
    # Compute metadata
    metadata = _compute_canvas_metadata(strokes_json)
    
    # Create canvas response record
    response = CanvasResponseModel(
        interview_id=interview_id,
        question_id=question_id,
        strokes_json=strokes_json,
        final_image_base64=image,
        duration_ms = metadata["duration"] * 1000,
        stroke_count = metadata["strokeCount"],
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    return {
        'status': 'ok',
        'response_id': response.id,
        'metadata': metadata,
        'created_at': response.created_at.isoformat() if response.created_at else None
    }


@router.post('/interviews/{interview_id}/canvas-submit')
def submit_canvas(
    interview_id: int,
    payload: CandidateCanvasSubmission,
    x_candidate_token: str | None = Header(None),
    db: Session = Depends(get_db)
):
    """
    Candidate submission of canvas drawing response (JSON payload version).
    Validates token and stores canvas response.
    """
    ok, interview = _validate_token(db, x_candidate_token, interview_id)
    if not ok:
        raise HTTPException(status_code=403, detail='Invalid candidate token')
    
        # Verify question exists and is canvas_drawing type
    question = db.query(QuestionModel).filter(QuestionModel.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail='Question not found')
    qtype = (question.type or '').lower()
    if qtype not in ("canvas_drawing", "sketch"):
        raise HTTPException(status_code=400, detail='Question is not a canvas_drawing type')

    
    # Prepare metadata
    metadata = {
        "duration": payload.duration,
        "strokeCount": payload.stroke_count,
        "submittedAt": datetime.now(timezone.utc).isoformat()
    }
    
    # Create canvas response record
    response = CanvasResponseModel(
        interview_id=interview_id,
        question_id=payload.question_id,
        strokes_json=payload.strokes,
        final_image_base64=payload.final_image,
        duration_ms = metadata["duration"] * 1000,
        stroke_count = metadata["strokeCount"],
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    return {
        'status': 'ok',
        'response_id': response.id,
        'created_at': response.created_at.isoformat() if response.created_at else None
    }