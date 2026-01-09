"""
Quick Start Guide: ML Pipeline Integration with FastAPI

This guide gets you up and running with the ML analysis integration in 5 minutes.
"""

# ============================================================================
# STEP 1: SETUP (One-time)
# ============================================================================

"""
1. Copy files to your project:
   ✅ backend/app/models/analysis.py
   ✅ backend/app/schemas_analysis.py
   ✅ ml/service/final_pipeline.py (updated)
   ✅ ml/service/analyzer.py (updated)
   ✅ backend/app/api/routes/interviews.py (updated)

2. Create database table:
   From backend/:
   > alembic revision --autogenerate -m "Add interview_analysis table"
   > alembic upgrade head
   
   OR manually in SQL:
   CREATE TABLE interview_analysis (
     id SERIAL PRIMARY KEY,
     interview_id INTEGER NOT NULL UNIQUE,
     status VARCHAR(20) DEFAULT 'pending',
     event_percentages TEXT,
     analysis_report TEXT,
     risk_level VARCHAR(20),
     effective_risk_percentage FLOAT,
     error_message TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP,
     FOREIGN KEY (interview_id) REFERENCES interviews(id)
   );

3. Install dependencies:
   pip install -r backend/requirements.txt
   
4. Update imports in backend/app/main.py (if needed):
   # Already imported via interviews router
"""


# ============================================================================
# STEP 2: BASIC USAGE
# ============================================================================

"""
Method A: Upload video + Auto-analyze
────────────────────────────────────
POST /interviews/{id}/complete-with-analysis

This is the recommended method. Combines recording upload with automatic
analysis triggering.

JavaScript example:
"""

# example_frontend.js
fetch('/interviews/42/complete-with-analysis', {
    method: 'POST',
    body: formData  # contains file, question_id, answer
})
.then(r => r.json())
.then(data => {
    console.log('Recording saved, analysis queued');
    console.log('Analysis ID:', data.analysis_id);
    // Now poll for results
})


"""
Method B: Manual analysis trigger
──────────────────────────────────
POST /interviews/{id}/analyze

Use this if video already exists and you want to re-analyze.
"""

fetch('/interviews/42/analyze', {method: 'POST'})
.then(r => r.json())
.then(data => console.log('Analysis queued, ID:', data.analysis_id))


"""
Method C: Check analysis status
─────────────────────────────────
GET /interviews/{id}/analysis

Poll this endpoint to get results. Status values:
- pending: Queued, waiting
- processing: Running
- completed: Done, results available
- failed: Error occurred
"""

fetch('/interviews/42/analysis')
.then(r => r.json())
.then(analysis => {
    if (analysis.status === 'completed') {
        console.log('Risk:', analysis.risk_level);
        console.log('Report:', analysis.analysis_report);
    }
})


# ============================================================================
# STEP 3: TESTING
# ============================================================================

"""
Test the integration:

1. Create an interview:
"""

curl -X POST http://localhost:8000/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Interview",
    "candidate_name": "John Doe",
    "candidate_email": "john@test.com",
    "scheduled_at": "2024-01-10T10:00:00Z",
    "duration_minutes": 30,
    "questions": [{"order": 1, "text": "Test Q?", "type": "coding"}]
  }'

# Response includes "id": 1


"""
2. Upload video and trigger analysis:
"""

curl -X POST http://localhost:8000/interviews/1/complete-with-analysis \
  -F "file=@sample_video.mp4" \
  -F "question_id=1" \
  -F "answer=My answer"

# Response: {"status": "ok", "analysis_queued": true, "analysis_id": 15}


"""
3. Poll for results (repeat every 10 seconds):
"""

curl http://localhost:8000/interviews/1/analysis

# While processing:
# {"status": "processing", ...}

# When done:
# {
#   "status": "completed",
#   "risk_level": "high",
#   "effective_risk_percentage": 75.5,
#   "analysis_report": "Based on gaze patterns...",
#   ...
# }


# ============================================================================
# STEP 4: FRONTEND INTEGRATION
# ============================================================================

"""
React Component Example:
"""

import { useState, useEffect } from 'react';

export function InterviewAnalysis({ interviewId }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // Trigger analysis
  async function handleAnalyze() {
    setLoading(true);
    const res = await fetch(`/interviews/${interviewId}/analyze`, {
      method: 'POST'
    });
    const data = await res.json();
    if (res.ok) {
      pollForResults();
    } else {
      alert('Error: ' + data.detail);
    }
  }

  // Poll for results
  async function pollForResults() {
    const maxAttempts = 60; // 10 minutes at 10s intervals
    
    for (let i = 0; i < maxAttempts; i++) {
      const res = await fetch(`/interviews/${interviewId}/analysis`);
      const data = await res.json();
      
      setAnalysis(data);
      
      if (data.status === 'completed' || data.status === 'failed') {
        setLoading(false);
        return;
      }
      
      // Wait 10 seconds before polling again
      await new Promise(r => setTimeout(r, 10000));
    }
    
    setLoading(false);
    alert('Analysis timeout');
  }

  if (!analysis) {
    return <button onClick={handleAnalyze}>Analyze Interview</button>;
  }

  return (
    <div>
      <p>Status: {analysis.status}</p>
      {analysis.status === 'completed' && (
        <>
          <p>Risk Level: {analysis.risk_level}</p>
          <p>Score: {analysis.effective_risk_percentage}%</p>
          <p>Report: {analysis.analysis_report}</p>
        </>
      )}
      {analysis.status === 'failed' && (
        <p>Error: {analysis.error_message}</p>
      )}
      {loading && <p>Processing...</p>}
    </div>
  );
}


# ============================================================================
# STEP 5: VERIFY IT'S WORKING
# ============================================================================

"""
1. Check backend logs:
   Look for lines like:
   - "Analysis queued for interview 1"
   - "Starting ML pipeline for interview 1"
   - "✅ ML pipeline completed for interview 1"

2. Check database:
   SELECT * FROM interview_analysis;
   
   Should show records with statuses:
   - pending (not started yet)
   - processing (currently running)
   - completed (done)
   - failed (error)

3. Check uploads directory:
   backend/uploads/ should contain video files
   events/ should contain gaze event JSON files
   
4. Check analysis results in database:
   SELECT risk_level, effective_risk_percentage FROM interview_analysis WHERE id=1;
"""


# ============================================================================
# STEP 6: CUSTOMIZE (OPTIONAL)
# ============================================================================

"""
Change timeout (in interviews.py, _run_ml_pipeline function):
"""

timeout=600  # Change to 300 for 5 minutes, 1800 for 30 minutes


"""
Auto-trigger analysis on interview completion:
In backend/app/api/routes/interviews.py, modify complete_interview endpoint:
"""

@router.post("/{interview_id}/complete")
def complete_interview(...):
    # Save recording...
    
    # Auto-trigger analysis
    if background_tasks:
        background_tasks.add_task(_run_ml_pipeline, interview_id, save_path)
    
    return response


"""
Disable background tasks (run synchronously for testing):
"""

# In _run_ml_pipeline function, remove the background_tasks.add_task()
# and call it directly: _run_ml_pipeline(interview_id, video_path)


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Q: Analysis is stuck in "processing"
A: Check logs for errors. Pipeline may have crashed silently.
   Run manual test: python -m ml.service.final_pipeline /path/to/video.mp4 1

Q: "Video file not found" error
A: Ensure video was uploaded successfully.
   Check backend/uploads/ directory.
   Verify file_path in recordings table.

Q: Analysis shows "timeout"
A: Video is too long or system too slow.
   Increase timeout in _run_ml_pipeline function.
   Optimize video resolution before upload.

Q: LLM analysis says "connection timeout"
A: LLM service (OpenAI/Anthropic) is down or slow.
   Check API key in .env
   Check network connectivity to LLM service

Q: Cannot import ml.service.final_pipeline
A: Ensure project root is in Python path.
   Run from project root directory.
   Check ml/__init__.py exists.
"""


# ============================================================================
# NEXT STEPS
# ============================================================================

"""
1. Read ML_INTEGRATION_GUIDE.md for detailed architecture
2. Run tests: pytest tests/test_ml_integration.py -v
3. Check logging in backend to debug issues
4. Review requirements.txt for all dependencies
5. Set up environment variables in .env
6. Deploy to production with proper error monitoring (Sentry/DataDog)
"""
