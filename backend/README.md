# Backend (berribot-interview)

This is a minimal FastAPI backend for Week 1.

Quick start:
```powershell
cd backend
python -m venv .venv; ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:
- GET / - health check
- POST /interviews - create interview (returns created record)
- GET /interviews - list interviews
- GET /interviews/{id} - get interview details

DB: SQLite (`berribot.db`) in the backend directory.
