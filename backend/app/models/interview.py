from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class Interview(Base):
    __tablename__ = 'interviews'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    candidate_name = Column(String, nullable=False)
    candidate_email = Column(String, nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    timezone = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(String, nullable=False, default='scheduled')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    token = Column(String(64), nullable=True, index=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
