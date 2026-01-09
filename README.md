
# berribot-interview (Week 1 - Nalin)

This workspace contains a minimal frontend and backend setup created to satisfy Week 1 goals.


Frontend: `frontend` (Vite + React)
Backend: `backend` (FastAPI + PostgreSQL)

Run the backend (PostgreSQL)
```powershell
cd backend
# create and activate a venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Use the venv python to install dependencies (avoid broken pip launchers)
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Configure the database connection. Create `backend/.env.postgres` with:
# DATABASE_URL=postgresql+psycopg://berribot:nalin@localhost:5432/berribot
# or export the env var in your shell:
$env:DATABASE_URL = 'postgresql+psycopg://berribot:nalin@localhost:5432/berribot'

# Start Postgres (choose one):
# - Use the included PowerShell helper:
.\start-postgres.ps1
# - Or use Docker compose (requires Docker):
docker-compose up -d

# Start the app (use venv python to avoid broken uvicorn.exe launcher):
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the frontend:
```powershell
cd frontend
npm install
npm run dev
```

Default API endpoint: http://localhost:8000
Default frontend: http://localhost:5173

Notes:
- This project expects a `DATABASE_URL` environment variable (or `backend/.env.postgres`) pointing to your Postgres server.
- For quick local testing you can use SQLite instead by setting:
	`$env:DATABASE_URL = 'sqlite:///./berribot.db'`
	but the canonical development configuration is Postgres.
- If you moved the repository, recreate the venv or invoke pip via `python -m pip` to avoid launchers with stale shebangs.
