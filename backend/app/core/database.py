from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///./berribot.db')

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith('sqlite') else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
