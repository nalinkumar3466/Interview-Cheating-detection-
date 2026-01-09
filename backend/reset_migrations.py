#!/usr/bin/env python
import os
from sqlalchemy import create_engine, text

os.environ['DATABASE_URL'] = 'postgresql+psycopg://berribot:nalin@localhost:5432/berribot'
db_url = os.environ['DATABASE_URL']

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Drop alembic_version table if exists
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
        print("✓ alembic_version table dropped")
except Exception as e:
    print(f"✗ Error: {e}")
