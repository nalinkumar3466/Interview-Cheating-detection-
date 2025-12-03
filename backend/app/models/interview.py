from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Interview(Base):
    __tablename__ = 'interviews'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    scheduled_at = Column(String, nullable=True)
