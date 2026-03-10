
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import interviews
from app.core.database import Base, engine
from dotenv import load_dotenv
from app.api.routes import admin

import os

load_dotenv()

import logging

logging.getLogger().info("DATABASE engine url: %s", getattr(engine, "url", "<unknown>"))


app = FastAPI(title='Berribot API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Add this line

)

app.include_router(admin.router)
app.include_router(interviews.router)
from app.api.routes.candidate import router as candidate_router
app.include_router(candidate_router)
from app.api.routes.canvas import router as canvas_router
app.include_router(canvas_router)


# Serve uploaded files under /uploads
from pathlib import Path
uploads_path = str(Path(__file__).resolve().parent.parent.parent.parent / 'uploads')
app.mount('/uploads', StaticFiles(directory=uploads_path), name='uploads')
canvas_uploads_path = "canvas-uploads"  # Relative path
app.mount('/canvas-uploads', StaticFiles(directory=canvas_uploads_path), name='canvas-uploads')
@app.get('/')
def root():
    return {'status': 'ok'}

@app.on_event('startup')
def on_startup():
    # create DB tables if they do not exist; handle DB connection errors gracefully
    from sqlalchemy.exc import OperationalError
    from pathlib import Path
    import sys

    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        logging.getLogger().error("Database connection failed during startup: %s", e)
        logging.getLogger().warning(
            "DB create skipped. Check your DATABASE_URL, database server, and credentials.\n"
            "If you are using Docker, ensure the DB container is running and the user/password match.\n"
            "You can export the URL temporarily: $env:DATABASE_URL = 'postgresql+psycopg://user:pass@host:5432/db'"
        )
        # Controlled behavior: only fail startup if ENSURE_DB_ON_STARTUP is set to '1'
        from os import getenv
        if getenv('ENSURE_DB_ON_STARTUP', '0') in ('1', 'true', 'True'):
            logging.getLogger().error('ENSURE_DB_ON_STARTUP is set; exiting due to DB error')
            sys.exit(1)
        else:
            logging.getLogger().warning('Continuing without DB schema creation. Some endpoints may fail until DB is reachable.')
    except Exception as e:
        logging.getLogger().exception("Unexpected error while creating DB tables: %s", e)
        from os import getenv
        if getenv('ENSURE_DB_ON_STARTUP', '0') in ('1', 'true', 'True'):
            sys.exit(1)
        logging.getLogger().warning('Continuing despite unexpected DB error; set ENSURE_DB_ON_STARTUP=1 to make startup fail on DB errors.')

    # ensure uploads folder exists at backend/uploads
    base_dir = Path(__file__).resolve().parent.parent  # backend/
    uploads = base_dir / 'uploads'
    uploads.mkdir(parents=True, exist_ok=True)

