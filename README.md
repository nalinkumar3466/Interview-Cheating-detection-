
# Interview Cheating Detection System

A comprehensive system for detecting cheating in video interviews using machine learning-based gaze tracking and behavior analysis.

## Components

- **Frontend**: React application with Vite for user interface
- **Backend**: FastAPI server with PostgreSQL database
- **ML Pipeline**: Computer vision and gaze tracking analysis

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL (optional, SQLite for testing)
pgcli -h localhost -p 5432 -U berribotuser -d berribot
uvicorn app.main:app --reload
### 1. Backend Setup

```bash
cd backend
python -m venv .venv

 .\.venv\Scripts\activate

$env:PYTHONPATH="N:\BERRIBOT\Interview-Cheating-detection\backend"
$env:DATABASE_URL = 'postgresql+psycopg://berribotuser:berribot@localhost:5432/berribot'
$env:OPENAI_API_KEY = "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"

.\start-postgres.ps1

# Start backend server
python -m uvicorn app.main:app --reload

```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

### 2. Frontend Setup & Run

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Expected Output**:
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

---

### 3. ML Pipeline Setup & Run

```powershell
cd ml

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install ML dependencies
pip install -r requirements.txt

#Go back to root 
cd.. 

$env:DATABASE_URL = 'postgresql+psycopg://berribotuser:berribot@localhost:5432/berribot'

# Initialize database (run once)
python -m ml.db.init_db
```

**Expected Output**:
```
✅ Database initialized successfully
```

Set OpenAI API key:
```powershell
$env:OPENAI_API_KEY = "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"
```

Run analysis on interview video:
```powershell
python -m ml.service.final_pipeline "samples/interviewsample1.mp4" 3
```

**Expected Output**:
```
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
2026-01-14 12:58:57,713 - __main__ - INFO - Starting analysis for interview 3
2026-01-14 12:58:57,713 - __main__ - INFO - Step 1: Analyzing video
2026-01-14 12:58:58,025 - __main__ - INFO - Video duration: 0.0s
2026-01-14 12:58:58,026 - __main__ - INFO - Step 2: Processing behavior events
2026-01-14 12:58:58,026 - __main__ - INFO - Events saved to events\interview_3_events.json
2026-01-14 12:58:58,026 - __main__ - INFO - Step 4: Computing effective risk
2026-01-14 12:58:58,026 - __main__ - INFO - Risk level: Low, Effective %: 0.00%
2026-01-14 12:58:58,026 - __main__ - INFO - Step 5: Generating LLM analysis
2026-01-14 12:58:58,199 - __main__ - INFO - ✅ Successfully analyzed interview 3

{"status": "success", "interview_id": 3, "risk_level": "Low", "effective_percentage": 0.0}
```

---

## Run Everything Together (3 Terminals)

**Terminal 1 - Start Backend**:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend**:
```powershell
cd frontend
npm run dev
```

**Terminal 3 - Run ML Analysis** (as needed):
```powershell
cd ml
.\.venv\Scripts\Activate.ps1
$env:OPENAI_API_KEY = "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"
python -m ml.service.final_pipeline "samples/interviewsample1.mp4" 3
```

Once started, access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Available Sample Videos

Located in `ml/samples/`:
- `interviewsample1.mp4` - Main interview video
- `center.mp4`, `left.mp4`, `right.mp4`, `down.mp4`, `up.mp4` - Gaze direction samples
- `reading.mp4`, `reading2.mp4` - Reading behavior samples
- `calibration.mp4` - Calibration video
- `blink.mp4` - Blink detection sample

---

## ML Pipeline Command Reference

Analyze a video:
```powershell
python -m ml.service.final_pipeline "<video_path>" <interview_id>
```

Examples:
```powershell
# Interview 1
python -m ml.service.final_pipeline "samples/center.mp4" 1

# Interview 3 
python -m ml.service.final_pipeline "samples/interviewsample1.mp4" 3

# Any custom video
python -m ml.service.final_pipeline "C:\path\to\video.mp4" 5
```

---

## Output Files & Results

After running ML pipeline:

**Gaze Tracking Data**:
```
ml/logs/interviewsample1.csv
```

**Behavior Events**:
```
ml/events/interview_3_events.json
```

**Event Types Detected**:
- Gaze directions: CENTER, LEFT, RIGHT, DOWN, UP, READING
- Suspicious behaviors: Frequent Distraction, Prolonged Looking Away
- Risk metrics: Low / Medium / High

---

## Database Configuration

### PostgreSQL (Recommended)

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://berribot:nalin@localhost:5432/berribot'
```

Start PostgreSQL:
```powershell
cd backend
.\start-postgres.ps1
```

### SQLite (Quick Testing)

```powershell
$env:DATABASE_URL = 'sqlite:///./berribot.db'
```

---

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'app'`
```powershell
# Make sure you're in backend directory and venv is activated
cd backend
.\.venv\Scripts\Activate.ps1
```

**Issue**: `pip install` fails
```powershell
# Use venv python directly
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Issue**: MediaPipe attribute error
```powershell
# Reinstall correct version
pip install --upgrade mediapipe==0.10.9
```

**Issue**: OpenAI API key not set
```powershell
$env:OPENAI_API_KEY = "your_key_here"
```

**Issue**: Port already in use
```powershell
# Backend running on different port
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001

# Frontend running on different port
npm run dev -- --port 5174
```

---

## ML Requirements

```
opencv-python==4.9.0.80
mediapipe==0.10.9
numpy==1.26.4
pandas
scipy
sqlalchemy
pydantic
fastapi
uvicorn
openai
python-dotenv
tqdm
```

---

## Notes

- Each component (Backend, Frontend, ML) requires its own virtual environment
- Database URL must be set before starting backend
- OpenAI API key required for ML analysis reports
- Sample videos in `ml/samples/` for testing
- ML pipeline outputs stored in `ml/logs/`, `ml/events/`, and database
