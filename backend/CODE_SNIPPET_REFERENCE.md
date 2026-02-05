"""
CODE SNIPPET REFERENCE
ML Pipeline Integration - Copy/Paste Examples

Use these code snippets for common tasks.
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. FRONTEND - REACT COMPONENT
# ═══════════════════════════════════════════════════════════════════════════

import { useState, useEffect } from 'react';

export function InterviewAnalysisComponent({ interviewId }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pollCount, setPollCount] = useState(0);

  // Upload video and queue analysis
  async function handleCompleteWithAnalysis(videoFile, questionId, answer) {
    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('question_id', questionId);
    formData.append('answer', answer);

    try {
      const response = await fetch(`/interviews/${interviewId}/complete-with-analysis`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      console.log('Recording saved, analysis queued:', data.analysis_id);
      
      // Start polling
      pollForResults();
    } catch (err) {
      setError('Upload failed: ' + err.message);
    }
  }

  // Poll for analysis results
  async function pollForResults() {
    setLoading(true);
    setError(null);
    setPollCount(0);

    const maxAttempts = 60; // 10 minutes at 10s intervals
    const pollInterval = 10000; // 10 seconds

    const poll = async () => {
      try {
        const response = await fetch(`/interviews/${interviewId}/analysis`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail);
        }

        setAnalysis(data);
        setPollCount(prev => prev + 1);

        // Stop polling if done
        if (data.status === 'completed' || data.status === 'failed') {
          setLoading(false);
          return;
        }

        // Continue polling if not done
        if (pollCount < maxAttempts) {
          setTimeout(poll, pollInterval);
        } else {
          setError('Analysis timeout (exceeded 10 minutes)');
          setLoading(false);
        }
      } catch (err) {
        setError('Polling failed: ' + err.message);
        setLoading(false);
      }
    };

    poll();
  }

  // Manually trigger analysis
  async function handleManualAnalysis() {
    try {
      const response = await fetch(`/interviews/${interviewId}/analyze`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      console.log('Analysis queued:', data.analysis_id);
      pollForResults();
    } catch (err) {
      setError('Failed to trigger analysis: ' + err.message);
    }
  }

  return (
    <div className="analysis-container">
      <h2>Interview Analysis</h2>

      {/* Upload Form */}
      {!loading && (!analysis || analysis.status === 'failed') && (
        <div className="upload-form">
          <input type="file" accept="video/*" id="videoFile" />
          <input type="number" placeholder="Question ID" id="questionId" />
          <textarea placeholder="Answer" id="answerText" />
          <button onClick={() => {
            const file = document.getElementById('videoFile').files[0];
            const qId = document.getElementById('questionId').value;
            const answer = document.getElementById('answerText').value;
            handleCompleteWithAnalysis(file, qId, answer);
          }}>
            Upload & Analyze
          </button>
          <button onClick={handleManualAnalysis}>
            Analyze Existing Recording
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading">
          <p>Analysis in progress... ({pollCount * 10}s elapsed)</p>
          <div className="progress-bar"></div>
        </div>
      )}

      {/* Results */}
      {analysis && !loading && (
        <div className="results">
          <h3>Status: {analysis.status}</h3>
          
          {analysis.status === 'completed' && (
            <>
              <div className={`risk-level ${analysis.risk_level}`}>
                Risk Level: <strong>{analysis.risk_level.toUpperCase()}</strong>
              </div>
              <p>Effective Risk: {analysis.effective_risk_percentage}%</p>
              <div className="report">
                <h4>Analysis Report:</h4>
                <p>{analysis.analysis_report}</p>
              </div>
            </>
          )}

          {analysis.status === 'failed' && (
            <div className="error">
              <strong>Analysis Failed</strong>
              <p>{analysis.error_message}</p>
            </div>
          )}

          {analysis.status === 'pending' && (
            <p>Queued and waiting to run...</p>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}


# ═══════════════════════════════════════════════════════════════════════════
# 2. BACKEND - MANUAL ANALYSIS TRIGGER (Python)
# ═══════════════════════════════════════════════════════════════════════════

# Example: Trigger analysis from a Celery task or another service

import requests
import json

def trigger_interview_analysis(interview_id: int, backend_url: str = "http://localhost:8000"):
    """Manually trigger analysis for an interview."""
    
    endpoint = f"{backend_url}/interviews/{interview_id}/analyze"
    
    try:
        response = requests.post(endpoint, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Analysis queued for interview {interview_id}")
        print(f"   Analysis ID: {data['analysis_id']}")
        return data
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def get_analysis_result(interview_id: int, backend_url: str = "http://localhost:8000"):
    """Fetch analysis results."""
    
    endpoint = f"{backend_url}/interviews/{interview_id}/analysis"
    
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            print(f"No analysis found for interview {interview_id}")
        raise


def wait_for_analysis(interview_id: int, max_wait_seconds: int = 600, poll_interval: int = 10):
    """Poll until analysis completes or timeout."""
    
    import time
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait_seconds:
            raise TimeoutError(f"Analysis timeout after {max_wait_seconds}s")
        
        result = get_analysis_result(interview_id)
        
        print(f"Status: {result['status']} (elapsed: {int(elapsed)}s)")
        
        if result['status'] == 'completed':
            print(f"\n✅ Analysis Complete!")
            print(f"   Risk Level: {result['risk_level']}")
            print(f"   Effective Risk: {result['effective_risk_percentage']}%")
            print(f"\n{result['analysis_report']}")
            return result
        
        elif result['status'] == 'failed':
            raise RuntimeError(f"Analysis failed: {result['error_message']}")
        
        time.sleep(poll_interval)


# Usage:
if __name__ == "__main__":
    interview_id = 42
    
    # Trigger analysis
    trigger_interview_analysis(interview_id)
    
    # Wait for results
    results = wait_for_analysis(interview_id)


# ═══════════════════════════════════════════════════════════════════════════
# 3. DATABASE - DIRECT QUERIES
# ═══════════════════════════════════════════════════════════════════════════

# Using SQLAlchemy

from app.core.database import SessionLocal
from app.models.analysis import InterviewAnalysis
from datetime import datetime, timedelta

db = SessionLocal()

# Get analysis for interview
analysis = db.query(InterviewAnalysis).filter(
    InterviewAnalysis.interview_id == 42
).first()

# Get all completed analyses from last 24 hours
recent_completed = db.query(InterviewAnalysis).filter(
    InterviewAnalysis.status == 'completed',
    InterviewAnalysis.created_at >= datetime.now() - timedelta(hours=24)
).all()

# Get failed analyses
failed = db.query(InterviewAnalysis).filter(
    InterviewAnalysis.status == 'failed'
).all()

# Get statistics
from sqlalchemy import func

stats = db.query(
    InterviewAnalysis.status,
    func.count(InterviewAnalysis.id).label('count'),
    func.avg(InterviewAnalysis.effective_risk_percentage).label('avg_risk')
).group_by(InterviewAnalysis.status).all()

for status, count, avg_risk in stats:
    print(f"{status}: {count} analyses, avg risk: {avg_risk:.1f}%")

db.close()


# ═══════════════════════════════════════════════════════════════════════════
# 4. TESTING - MANUAL TEST SCRIPT
# ═══════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python
"""Manual test script for ML integration."""

import requests
import json
import time
import tempfile
import sys

BASE_URL = "http://localhost:8000"

def test_create_interview():
    """Test: Create interview"""
    print("\\n1️⃣  Creating interview...")
    
    payload = {
        "title": "Test Interview",
        "candidate_name": "Test User",
        "candidate_email": "test@example.com",
        "scheduled_at": "2024-01-10T10:00:00Z",
        "duration_minutes": 30,
        "questions": [
            {"order": 1, "text": "What's your experience?", "type": "coding"},
            {"order": 2, "text": "Explain your approach", "type": "explain"}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/interviews", json=payload)
    assert response.status_code == 201, f"Failed: {response.text}"
    
    interview = response.json()
    print(f"✅ Created interview ID: {interview['id']}")
    return interview['id']


def test_upload_and_analyze(interview_id):
    """Test: Upload video and trigger analysis"""
    print(f"\\n2️⃣  Uploading video for interview {interview_id}...")
    
    # Create fake video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b'fake video data for testing')
        video_path = f.name
    
    try:
        with open(video_path, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/interviews/{interview_id}/complete-with-analysis",
                files={'file': f},
                data={'question_id': 1, 'answer': 'Test answer'}
            )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        print(f"✅ Recording saved, analysis_id: {data['analysis_id']}")
        return data['analysis_id']
    
    finally:
        import os
        os.unlink(video_path)


def test_poll_analysis(interview_id, max_wait=120):
    """Test: Poll for analysis results"""
    print(f"\\n3️⃣  Polling for analysis results (max wait: {max_wait}s)...")
    
    start = time.time()
    
    while True:
        elapsed = int(time.time() - start)
        
        response = requests.get(f"{BASE_URL}/interviews/{interview_id}/analysis")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        analysis = response.json()
        status = analysis['status']
        
        print(f"   Status: {status} ({elapsed}s elapsed)")
        
        if status == 'completed':
            print(f"✅ Analysis completed!")
            print(f"   Risk Level: {analysis['risk_level']}")
            print(f"   Risk %: {analysis['effective_risk_percentage']}%")
            return analysis
        
        elif status == 'failed':
            print(f"❌ Analysis failed: {analysis['error_message']}")
            return analysis
        
        if elapsed > max_wait:
            print(f"⚠️  Timeout after {max_wait}s (still {status})")
            return analysis
        
        time.sleep(10)


def run_full_test():
    """Run complete test workflow"""
    print("=" * 60)
    print("ML INTEGRATION TEST")
    print("=" * 60)
    
    try:
        interview_id = test_create_interview()
        analysis_id = test_upload_and_analyze(interview_id)
        results = test_poll_analysis(interview_id)
        
        print("\\n" + "=" * 60)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_full_test()


# ═══════════════════════════════════════════════════════════════════════════
# 5. DOCKER - RUN ML PIPELINE LOCALLY
# ═══════════════════════════════════════════════════════════════════════════

# Dockerfile.ml
# Use for running ML pipeline in isolation

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    libsm6 libxext6 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run pipeline
ENTRYPOINT ["python", "-m", "ml.service.final_pipeline"]
CMD ["--help"]


# Usage:
# docker build -f Dockerfile.ml -t ml-pipeline .
# docker run ml-pipeline /path/to/video.mp4 42


# ═══════════════════════════════════════════════════════════════════════════
# 6. CURL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════

# Create interview
curl -X POST http://localhost:8000/interviews \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Test Interview",
    "candidate_name": "John Doe",
    "candidate_email": "john@test.com",
    "scheduled_at": "2024-01-10T10:00:00Z",
    "duration_minutes": 30,
    "questions": [{"order": 1, "text": "Q1?", "type": "coding"}]
  }'

# Upload video and trigger analysis
curl -X POST http://localhost:8000/interviews/1/complete-with-analysis \\
  -F "file=@sample_video.mp4" \\
  -F "question_id=1" \\
  -F "answer=My answer"

# Get analysis results
curl http://localhost:8000/interviews/1/analysis

# Pretty print JSON response
curl -s http://localhost:8000/interviews/1/analysis | jq '.'


# ═══════════════════════════════════════════════════════════════════════════
# 7. ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════════════════

# .env file template

DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/interview_db
FRONTEND_BASE=http://localhost:5173
ML_PIPELINE_TIMEOUT=600
ML_LOG_LEVEL=INFO
LOG_LEVEL=INFO

# Optional: Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=noreply@yourapp.com

# Optional: LLM
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4


# ═══════════════════════════════════════════════════════════════════════════
# 8. LOGGING - VIEW ANALYSIS LOGS
# ═══════════════════════════════════════════════════════════════════════════

# View all analysis logs
grep "analysis" /var/log/berribot/backend.log

# View analysis for specific interview
grep "interview_42" /var/log/berribot/backend.log

# Watch logs in real-time
tail -f /var/log/berribot/backend.log | grep "analysis\\|interview_42"

# Count failed analyses
grep "status.*failed" /var/log/berribot/backend.log | wc -l

# Export logs for analysis
grep "analysis" /var/log/berribot/backend.log > analysis_logs.txt


# ═══════════════════════════════════════════════════════════════════════════
# 9. DEBUGGING - MANUAL PIPELINE RUN
# ═══════════════════════════════════════════════════════════════════════════

# Run pipeline manually to debug
cd /path/to/project
python -m ml.service.final_pipeline /path/to/video.mp4 42

# Expected output (on success):
# {
#   "status": "success",
#   "interview_id": 42,
#   "risk_level": "high",
#   "effective_percentage": 75.5
# }

# With verbose logging
LOGLEVEL=DEBUG python -m ml.service.final_pipeline /path/to/video.mp4 42


# ═══════════════════════════════════════════════════════════════════════════
# 10. PERFORMANCE - MEASURE ANALYSIS TIME
# ═══════════════════════════════════════════════════════════════════════════

import time
import subprocess
import sys

def benchmark_analysis(video_path: str, interview_id: int):
    """Measure ML pipeline execution time."""
    
    start = time.time()
    
    result = subprocess.run(
        [sys.executable, "-m", "ml.service.final_pipeline", video_path, str(interview_id)],
        capture_output=True,
        text=True
    )
    
    elapsed = time.time() - start
    
    print(f"Execution time: {elapsed:.1f}s")
    print(f"Return code: {result.returncode}")
    
    if result.returncode == 0:
        import json
        output = json.loads(result.stdout)
        print(f"Risk level: {output.get('risk_level')}")
    else:
        print(f"Error: {result.stderr}")


if __name__ == "__main__":
    benchmark_analysis("/path/to/video.mp4", 42)

"""
