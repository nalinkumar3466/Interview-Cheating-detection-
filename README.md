
# berribot-interview (Week 1 - Nalin)

This workspace contains a minimal frontend and backend setup created to satisfy Week 1 goals.


Frontend: `frontend` (Vite + React)
Backend: `backend` (FastAPI + SQLite)

Run the backend:
```powershell
cd backend
python -m venv .venv; ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:DATABASE_URL = 'postgresql+psycopg://berribot:nalin@localhost:5432/berribot'

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the frontend:
```powershell
cd frontend
npm install
npm run dev
```

Default API endpoint: http://localhost:8000
Default frontend: http://localhost:5173

Note: The frontend `Dashboard` fetches `/interviews` and shows scheduled interviews. Schedule page posts to `/interviews`. SQLite `berribot.db` is used in the backend folder for development.
