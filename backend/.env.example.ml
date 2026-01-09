# ML Pipeline Integration Configuration
# Place in backend/.env or backend/.env.production

# Database
DATABASE_URL=postgresql+psycopg://interview_user:secure_password@localhost:5432/interview_db

# Frontend
FRONTEND_BASE=http://localhost:5173

# ML Pipeline Execution
ML_PIPELINE_TIMEOUT=600  # seconds (10 minutes)
ML_LOG_LEVEL=INFO
ML_ENABLE_BACKGROUND_ANALYSIS=true

# Video Processing
VIDEO_MAX_SIZE=500000000  # 500MB in bytes
VIDEO_ALLOWED_FORMATS=.mp4,.avi,.mov,.mkv

# LLM Configuration (for analysis report generation)
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4
LLM_TIMEOUT=30

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=noreply@berribot.ai

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/berribot/backend.log

# Performance Tuning
WORKER_THREADS=4
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Feature Flags
ENABLE_ML_ANALYSIS=true
ENABLE_AUTO_ANALYSIS_ON_COMPLETE=true
ENABLE_LLM_REPORTS=true
