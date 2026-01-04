from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.interview import Interview as InterviewModel
from app.models.question import Question as QuestionModel
from app.models.recording import Recording
from app.models.candidatelog import CandidateLog
import os, time
from datetime import datetime, timezone

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
