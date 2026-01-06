from app.core.database import engine, Base
from app.models import Interview, Recording, Question
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done")
