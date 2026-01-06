from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ml.db.models import Base

DATABASE_URL = "sqlite:///analysis.db"  # replace later if needed

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
