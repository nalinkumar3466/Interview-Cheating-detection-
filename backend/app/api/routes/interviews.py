from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db, engine, Base
from app.models.interview import Interview as InterviewModel
from app.schemas import InterviewCreate, Interview

router = APIRouter(prefix="/interviews", tags=["interviews"]) 
logger = logging.getLogger(__name__)
@router.post("/", response_model=Interview, status_code=201)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db)):
    logger.info('Received create_interview payload: %s', payload.json())
    # If the client sends `assessment` instead of `title`, map it
    final_title = payload.title or getattr(payload, 'assessment', None)
    new_interview = InterviewModel(title=final_title, scheduled_at=payload.scheduled_at)
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    return new_interview

@router.get("/", response_model=List[Interview])
def list_interviews(db: Session = Depends(get_db)):
    items = db.query(InterviewModel).all()
    return items

@router.get("/{interview_id}", response_model=Interview)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    item = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Interview not found')
    return item
