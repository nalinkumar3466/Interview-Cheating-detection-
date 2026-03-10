from sqlalchemy import Column, Integer, Text, Float
from sqlalchemy.dialects.postgresql import JSON
from app.database import Base

class SketchAnswer(Base):
    __tablename__ = "sketch_answers"

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer)
    question_id = Column(Integer)
    strokes_json = Column(JSON)
    image_base64 = Column(Text)
    score = Column(Float)
    feedback = Column(Text)