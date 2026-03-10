from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.canvas_response import CanvasResponse as CanvasResponseModel

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/canvas/{response_id}/grade")
def grade_canvas_response(
    response_id: int,
    structure_score: float = Body(...),
    clarity_score: float = Body(...),
    completeness_score: float = Body(...),
    feedback: str = Body(None),
    db: Session = Depends(get_db)
):
    response = db.query(CanvasResponseModel).filter(
        CanvasResponseModel.id == response_id
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