# test_conn.py
import os, traceback
from pathlib import Path
from sqlalchemy import create_engine
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
env_postgres = ROOT / '.env.postgres'
if load_dotenv and env_postgres.exists():
    load_dotenv(env_postgres)

u = os.getenv("DATABASE_URL")
if not u:
    raise RuntimeError("DATABASE_URL is not set. Please set it or create backend/.env.postgres with the connection URL.")

print("Testing", u)
try:
    engine = create_engine(u)
    with engine.connect() as conn:
        print("OK: connected")
except Exception:
    print("ERROR:")
    traceback.print_exc()