from fastapi import APIRouter, UploadFile, File
import os
import shutil

from ai_scoring_pipeline.pipeline import run_pipeline

router = APIRouter()

UPLOAD_DIR = "uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    video_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = run_pipeline(video_path)

    return {
        "filename": file.filename,
        "segments": result
    }