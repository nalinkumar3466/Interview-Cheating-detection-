# PowerShell dev script: create venv, install deps, and run uvicorn
python -m venv .venv; ; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
