$env:DATABASE_URL="postgresql+psycopg://berribotuser:berribot@localhost:5432/berribot"
uvicorn app.main:app --reload
