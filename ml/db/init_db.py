from ml.db.database import Base, engine
from ml.db import models    # noqa: F401 (needed to register SQLAlchemy models)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

if __name__ == "__main__":
    init_db()
