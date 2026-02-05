from sqlalchemy import create_engine
import os

print(os.getenv("DATABASE_URL"))

engine = create_engine(os.getenv("DATABASE_URL"))
conn = engine.connect()
print("CONNECTED OK")
conn.close()
