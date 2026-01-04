from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.core.database import Base


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    examples = Column(Text, nullable=True)
    type = Column(String, nullable=True)
