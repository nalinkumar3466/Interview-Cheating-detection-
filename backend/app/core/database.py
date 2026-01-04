# backend/app/core/database.py
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Try to load dotenv from backend/.env.postgres if present, then from the environment.
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
env_postgres = ROOT / '.env.postgres'
if load_dotenv and env_postgres.exists():
    # load .env.postgres into environment so DATABASE_URL becomes available
    load_dotenv(env_postgres)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set. Set it to your Postgres connection string before starting the app.\n"
        "You can create a file named '.env.postgres' in the backend folder with:\n"
        "DATABASE_URL=postgresql+psycopg://user:password@host:5432/berribot\n"
        "Or export the env var in your shell before running uvicorn."
    )

# create engine for Postgres (SQLAlchemy will accept either postgresql:// or postgresql+psycopg://)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
