from sqlalchemy import create_engine, text
import os, traceback

# prefer DATABASE_URL if set
url = os.environ.get("DATABASE_URL") or "postgresql+psycopg://berribot:nalin@localhost:5432/berribot"
engine = create_engine(url)
try:
    with engine.connect() as conn:
        # SQLAlchemy 2.x requires text() for textual SQL or use exec_driver_sql
        result = conn.execute(text("select 1"))
        val = result.scalar()
        print("OK: connected, test query returned", val)
except Exception:
    print("ERROR:")
    traceback.print_exc()
