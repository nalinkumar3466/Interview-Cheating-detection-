# backend/app.py
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from .database import engine, SessionLocal, Base
from .models import Interview
from fastapi.middleware.cors import CORSMiddleware
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Berribot Interview API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InterviewCreate(BaseModel):
    title: str = None

@app.post("/api/interviews")
def create_interview(payload: InterviewCreate):
    db = SessionLocal()
    it = Interview(title=payload.title)
    db.add(it); db.commit(); db.refresh(it)
    db.close()
    return {"id": it.id, "title": it.title}

@app.get("/api/interviews")
def list_interviews():
    db = SessionLocal()
    items = db.query(Interview).all()
    db.close()
    return [{"id": it.id, "title": it.title, "created_at": it.created_at.isoformat()} for it in items]

@app.post("/api/upload-clip")
async def upload_clip(segment: UploadFile = File(...), interview_id: int = Form(...), ts_start: float = Form(...)):
    os.makedirs("uploads", exist_ok=True)
    fn = os.path.join("uploads", segment.filename)
    contents = await segment.read()
    with open(fn, "wb") as f:
        f.write(contents)
    return {"ok": True, "url": fn}
