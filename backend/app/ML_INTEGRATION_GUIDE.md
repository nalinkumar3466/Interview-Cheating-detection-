"""
FastAPI ML Pipeline Integration Guide
======================================

This module provides production-ready integration between FastAPI backend and Python ML pipeline.

## Overview

The system consists of:
1. **ML Pipeline** (ml/service/final_pipeline.py) - Video analysis with gaze tracking & behavior detection
2. **FastAPI Backend** (app/api/routes/interviews.py) - REST API with async background tasks
3. **Database Models** (app/models/analysis.py) - Analysis result storage
4. **Subprocess Management** - Safe execution with error handling and timeouts

## Architecture

┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
├─────────────────────────────────────────────────────────────┤
│  POST /interviews/{id}/complete-with-analysis               │
│  └─ Saves recording + queues ML pipeline analysis            │
│                                                               │
│  POST /interviews/{id}/analyze                              │
│  └─ Manually trigger analysis for existing interview         │
│                                                               │
│  GET /interviews/{id}/analysis                              │
│  └─ Fetch analysis results (pending/processing/completed)    │
└─────────────────────────────────────────────────────────────┘
            ↓ (subprocess.run, timeout=600s)
┌─────────────────────────────────────────────────────────────┐
│              Python ML Pipeline (Background Task)            │
├─────────────────────────────────────────────────────────────┤
│  ml.service.final_pipeline.analyze_interview()              │
│  1. Video → Gaze CSV (ml.temporal_smoothing)                │
│  2. CSV → Behavior Events (ml.process_behavior_from_csv)    │
│  3. Events → Risk Percentages (event_percentage_calculator) │
│  4. LLM Analysis Generation (llm_client)                    │
│  5. DB Storage (analyzer.store_analysis_result)             │
└─────────────────────────────────────────────────────────────┘
            ↓ (JSON output to stdout)
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Backend Database                      │
├─────────────────────────────────────────────────────────────┤
│  interviews_analysis table:                                 │
│  - id, interview_id, status, event_percentages              │
│  - analysis_report, risk_level, effective_risk_percentage   │
│  - error_message, created_at, updated_at                    │
└─────────────────────────────────────────────────────────────┘


## API Endpoints

### 1. Complete Interview + Auto-Analyze
POST /interviews/{interview_id}/complete-with-analysis

Request:
```
POST /interviews/42/complete-with-analysis
Content-Type: multipart/form-data

file: <video_file.mp4>
answer: "My answer to the question"
question_id: 1
```

Response (202 Accepted):
```json
{
  "status": "ok",
  "recording_id": 99,
  "file_path": "/backend/uploads/interview_42_1704897600_video.mp4",
  "analysis_queued": true,
  "analysis_id": 15
}
```

Flow:
- Saves video file to backend/uploads/
- Creates Recording DB entry
- Creates InterviewAnalysis record with status='pending'
- Queues background task to run ML pipeline
- Returns immediately (async)


### 2. Manually Trigger Analysis
POST /interviews/{interview_id}/analyze

Request:
```
POST /interviews/42/analyze
```

Response (200 OK):
```json
{
  "status": "queued",
  "interview_id": 42,
  "analysis_id": 15,
  "message": "Analysis scheduled. Results will be available shortly."
}
```

Behavior:
- Finds latest recording for interview
- Creates/updates InterviewAnalysis with status='pending'
- Queues background ML pipeline task
- Returns immediately


### 3. Fetch Analysis Results
GET /interviews/{interview_id}/analysis

Request:
```
GET /interviews/42/analysis
```

Response (200 OK):
```json
{
  "id": 15,
  "interview_id": 42,
  "status": "completed",
  "risk_level": "high",
  "effective_risk_percentage": 67.5,
  "event_percentages": "{\"suspicious_gaze_shift\":45.2,\"blink_pattern\":30.1,...}",
  "analysis_report": "Based on gaze analysis...",
  "error_message": null,
  "created_at": "2024-01-09T10:30:45.123Z",
  "updated_at": "2024-01-09T10:35:20.456Z"
}
```

Status values:
- `pending`: Queued, waiting to run
- `processing`: Currently running pipeline
- `completed`: Analysis done, results available
- `failed`: Error occurred (check error_message)


## Frontend Integration Example

```javascript
// React hook for analysis workflow
async function scheduleInterviewWithAnalysis(videoFile, questionId, answer) {
  // 1. Upload and queue analysis
  const formData = new FormData();
  formData.append('file', videoFile);
  formData.append('question_id', questionId);
  formData.append('answer', answer);
  
  const completeRes = await fetch(`/api/interviews/${interviewId}/complete-with-analysis`, {
    method: 'POST',
    body: formData
  });
  
  const { analysis_id } = await completeRes.json();
  
  // 2. Poll for results
  let analysis = null;
  for (let i = 0; i < 60; i++) {
    const analysisRes = await fetch(`/api/interviews/${interviewId}/analysis`);
    analysis = await analysisRes.json();
    
    if (analysis.status === 'completed' || analysis.status === 'failed') {
      break;
    }
    
    // Wait 10 seconds before polling again
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  
  // 3. Display results
  if (analysis.status === 'completed') {
    console.log(`Risk Level: ${analysis.risk_level}`);
    console.log(`Effective Risk: ${analysis.effective_risk_percentage}%`);
    console.log(analysis.analysis_report);
  } else if (analysis.status === 'failed') {
    console.error(`Analysis failed: ${analysis.error_message}`);
  }
}
```


## CLI Usage (Manual Testing)

```bash
# From project root
python -m ml.service.final_pipeline /path/to/video.mp4 42

# Output on success:
# {
#   "status": "success",
#   "interview_id": 42,
#   "risk_level": "high",
#   "effective_percentage": 67.5
# }

# Output on error:
# {
#   "status": "error",
#   "interview_id": 42,
#   "error": "CSV not found: /path/to/gaze.csv"
# }
```


## Error Handling

### Pipeline Execution Errors

**Timeout (>10 minutes)**
```json
{
  "status": "failed",
  "error_message": "Pipeline execution timeout (>10 minutes)",
  "error_code": "TIMEOUT"
}
```

**Video Processing Error**
```json
{
  "status": "failed",
  "error_message": "CSV not generated: /path/to/gaze.csv",
  "error_code": "CSV_NOT_FOUND"
}
```

**LLM Service Unavailable**
```json
{
  "status": "failed",
  "error_message": "LLM API connection timeout",
  "error_code": "LLM_ERROR"
}
```


## Database Schema

### interview_analysis table
```sql
CREATE TABLE interview_analysis (
  id INTEGER PRIMARY KEY,
  interview_id INTEGER NOT NULL UNIQUE,
  status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
  event_percentages TEXT,  -- JSON string
  analysis_report TEXT,
  risk_level VARCHAR(20),  -- low, medium, high
  effective_risk_percentage FLOAT,
  error_message TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (interview_id) REFERENCES interviews(id)
);
```


## Configuration

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/interview_db

# ML Pipeline (optional)
ML_TIMEOUT=600  # seconds
ML_LOG_LEVEL=INFO
```

### Subprocess Configuration
Location: app/api/routes/interviews.py (_run_ml_pipeline function)

```python
# Timeout for ML pipeline execution
timeout=600  # 10 minutes

# Working directory for subprocess
cwd=project_root  # Auto-detected from __file__

# Python module execution
cmd = [sys.executable, "-m", "ml.service.final_pipeline", video_path, interview_id]
```


## Logging

All operations are logged with structured logging:

```
2024-01-09 10:30:45 - app.api.routes.interviews - INFO - Analysis queued for interview 42
2024-01-09 10:30:46 - app.api.routes.interviews - INFO - Starting ML pipeline for interview 42
2024-01-09 10:35:20 - app.api.routes.interviews - INFO - ✅ ML pipeline completed for interview 42
```

### View Logs
```bash
# Backend logs
docker logs <container_id> -f

# Or in uvicorn terminal
# Look for "analysis", "pipeline", interview_id in output
```


## Testing

### Unit Test: Endpoint
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_trigger_analysis():
    response = client.post("/interviews/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["interview_id"] == 1
```

### Integration Test: Full Pipeline
```python
import json

# 1. Create interview
interview = client.post("/interviews", json={
    "title": "Test",
    "candidate_name": "John",
    "candidate_email": "john@test.com",
    "scheduled_at": "2024-01-10T10:00:00Z",
    "duration_minutes": 30,
    "questions": [{"order": 1, "text": "Q1?", "type": "coding"}]
}).json()

# 2. Upload recording
with open("test_video.mp4", "rb") as f:
    response = client.post(
        f"/interviews/{interview['id']}/complete-with-analysis",
        files={"file": f}
    )
    assert response.status_code == 200
    assert response.json()["analysis_queued"] is True

# 3. Poll for results (in real scenario, wait 5-10 minutes)
analysis = client.get(f"/interviews/{interview['id']}/analysis").json()
assert analysis["status"] in ["pending", "processing", "completed"]
```


## Troubleshooting

### Issue: "Video file not found"
**Cause**: Recording not saved or incorrect file path
**Solution**: Check /backend/uploads/ directory, verify POST complete-with-analysis succeeded

### Issue: "Analysis already in progress"
**Cause**: Tried to trigger analysis while it's running
**Solution**: Wait for previous analysis to complete, check status with GET /analysis

### Issue: "Pipeline execution timeout"
**Cause**: Complex video taking >10 minutes to analyze
**Solution**: Increase timeout in _run_ml_pipeline function or optimize video file

### Issue: "CSV not found" or "gaze tracking failed"
**Cause**: Video incompatible with gaze tracking model
**Solution**: Ensure video is clear, well-lit, shows candidate's face; check ml logs

### Issue: Database connection errors
**Cause**: backend and ML DB not synced or DATABASE_URL incorrect
**Solution**: Verify PostgreSQL running, check connection string in .env


## Performance Metrics

Typical execution times (with i7 CPU, 16GB RAM):

- **Gaze tracking**: 10-30 seconds (depends on video length)
- **Behavior analysis**: 5-10 seconds
- **Event calculation**: 2-5 seconds
- **LLM analysis**: 15-30 seconds
- **Total pipeline**: ~30-75 seconds (1-2 minute videos)

Complex videos (5+ minutes, poor lighting) may take 3-5 minutes.


## Production Deployment

### Docker Setup
```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Ensure uploads directory exists
RUN mkdir -p backend/uploads

# Run migrations
RUN alembic upgrade head

# Start backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes CronJob (Optional: Batch Analysis)
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ml-analysis-batch
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ml-pipeline
            image: app:latest
            command:
            - python
            - -m
            - ml.service.final_pipeline
            - /path/to/video.mp4
            - "0"
```

### Load Testing
```bash
# Generate 10 concurrent analysis requests
locust -f tests/locustfile.py --headless -u 10 -r 2 -t 60s

# Monitor DB connections
SELECT count(*) FROM pg_stat_activity;
```


## Future Improvements

1. **Caching**: Cache gaze tracking CSVs to skip duplicate analysis
2. **Queue System**: Use Celery/Redis for robust task queueing
3. **Parallel Processing**: Process multiple videos simultaneously
4. **Webhook Notifications**: Notify frontend when analysis completes
5. **Result Streaming**: Stream large result files via chunked responses
6. **Model Updates**: Support multiple gaze/behavior model versions
7. **Cost Optimization**: Batch LLM requests for efficiency
8. **API Rate Limiting**: Prevent abuse of analysis endpoints

"""
