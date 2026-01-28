# backend/app/core/database.py

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Try to load dotenv from backend/.env.postgres if present
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# Resolve backend root
ROOT = Path(__file__).resolve().parent.parent

# Load .env.postgres if exists
env_postgres = ROOT / '.env.postgres'
if load_dotenv and env_postgres.exists():
    load_dotenv(env_postgres)

# Read DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set. Set it to your Postgres connection string before starting the app.\n"
        "Create backend/.env.postgres with:\n"
        "DATABASE_URL=postgresql+psycopg://user:password@host:5432/berribot\n"
        "Or export it in your shell."
    )

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
