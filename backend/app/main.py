from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import interviews
from app.core.database import Base, engine

app = FastAPI(title='Berribot API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interviews.router)

@app.get('/')
def root():
    return {'status': 'ok'}

@app.on_event('startup')
def on_startup():
    Base.metadata.create_all(bind=engine)
