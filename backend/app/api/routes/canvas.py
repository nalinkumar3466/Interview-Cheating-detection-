"""
Canvas Drawing Question API Routes

Handles submission and retrieval of canvas drawing responses for interview questions.
Includes rubric-based grading and stroke timeline management.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime, timezone
from typing import List

from app.core.database import get_db
from app.models.canvas_response import CanvasResponse as CanvasResponseModel
from app.models.interview import Interview as InterviewModel
from app.models.question import Question as QuestionModel
from app.schemas import CanvasSubmitPayload, CanvasResponseOut, CanvasRubric

router = APIRouter(prefix="/interviews", tags=["canvas"])
logger = logging.getLogger(__name__)


def _compute_overall_score(structure: float | None, clarity: float | None, completeness: float | None) -> float | None:
    """Compute overall score as average of rubric scores."""
    scores = [s for s in [structure, clarity, completeness] if s is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


@router.post("/{interview_id}/canvas-submit", response_model=CanvasResponseOut, status_code=201)
def submit_canvas_response(
    interview_id: int,
    payload: CanvasSubmitPayload,
    db: Session = Depends(get_db)
):
    """
    Submit a canvas drawing response for a question.
    
    Expects:
    - question_id: ID of the canvas_drawing question
    - strokes: Array of stroke objects with tool, color, width, and points
    - final_image: Base64-encoded PNG of the final drawing
    - duration: Duration of drawing session (seconds)
    - stroke_count: Total number of strokes
    
    Returns: Stored canvas response with ID and timestamps
    """
    
    # Verify interview exists
    interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Verify question exists and is canvas_drawing type
    question = db.query(QuestionModel).filter(QuestionModel.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        qtype = (question.type or '').lower()
    qtype = (question.type or '').lower()
    if qtype not in ("canvas_drawing", "sketch"):
        raise HTTPException(status_code=400, detail="Question is not a canvas_drawing type")

    
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
        strokes_json=[s.model_dump() for s in payload.strokes],
        final_image_base64=payload.final_image,
        duration_ms = metadata["duration"] * 1000,
        stroke_count = metadata["strokeCount"],
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    logger.info(
        f"Canvas response submitted: interview={interview_id}, question={payload.question_id}, "
        f"strokes={len(payload.strokes)}"
    )
    
    return response


@router.get("/{interview_id}/canvas-responses", response_model=List[CanvasResponseOut])
def get_canvas_responses(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve all canvas responses for an interview.
    """
    
    # Verify interview exists
    interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    responses = db.query(CanvasResponseModel).filter(
        CanvasResponseModel.interview_id == interview_id
    ).all()
    
    return responses


@router.get("/{interview_id}/canvas-responses/{response_id}", response_model=CanvasResponseOut)
def get_canvas_response(
    interview_id: int,
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific canvas response by ID.
    """
    
    response = db.query(CanvasResponseModel).filter(
        CanvasResponseModel.id == response_id,
        CanvasResponseModel.interview_id == interview_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Canvas response not found")
    
    return response

@router.post("/{interview_id}/canvas-responses/{response_id}/grade")
def grade_canvas_response(
    interview_id: int,
    response_id: int,
    structure_score: float = Body(...),
    clarity_score: float = Body(...),
    completeness_score: float = Body(...),
    feedback: str = Body(None),
    db: Session = Depends(get_db)
):
    response = db.query(CanvasResponseModel).filter(
        CanvasResponseModel.id == response_id,
        CanvasResponseModel.interview_id == interview_id
    ).first()

    if not response:
        raise HTTPException(status_code=404, detail="Canvas response not found")

    overall = round(
        (structure_score + clarity_score + completeness_score) / 3,
        2
    )

    response.structure_score = structure_score
    response.clarity_score = clarity_score
    response.completeness_score = completeness_score
    response.overall_score = overall
    response.rubric_feedback = feedback

    db.commit()
    db.refresh(response)

    return {
        "status": "graded",
        "overall_score": overall
    }

@router.get("/{interview_id}/canvas-responses/{response_id}/playback")
def get_canvas_playback(
    interview_id: int,
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    Get canvas response data for stroke playback/replay.
    
    Returns strokes timeline and metadata for frontend replay functionality.
    """
    
    response = db.query(CanvasResponseModel).filter(
        CanvasResponseModel.id == response_id,
        CanvasResponseModel.interview_id == interview_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Canvas response not found")
    
    return {
        "response_id": response.id,
        "strokes": response.strokes_json or [],
        "metadata": {
                "strokeCount": response.stroke_count,
                "duration": int(response.duration_ms / 1000) if response.duration_ms else None
            },
        "submitted_at": response.created_at.isoformat() if response.created_at else None
    }
