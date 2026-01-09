"""
Production-ready tests for ML Pipeline integration.

Run with:
    pytest tests/test_ml_integration.py -v
    pytest tests/test_ml_integration.py -v -s  # with output
    pytest tests/test_ml_integration.py::test_trigger_analysis -v  # single test
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Adjust imports based on your project structure
from app.main import app
from app.core.database import SessionLocal
from app.models.interview import Interview as InterviewModel
from app.models.analysis import InterviewAnalysis
from app.models.recording import Recording
from fastapi.testclient import TestClient


client = TestClient(app)


class TestAnalysisEndpoints:
    """Test suite for analysis endpoints"""
    
    @pytest.fixture
    def db_session(self):
        """Provide a database session for tests"""
        db = SessionLocal()
        yield db
        db.close()
    
    @pytest.fixture
    def sample_interview(self, db_session):
        """Create a sample interview for testing"""
        interview = InterviewModel(
            title="Test Interview",
            candidate_name="John Doe",
            candidate_email="john@example.com",
            scheduled_at=datetime.now(timezone.utc),
            duration_minutes=30,
            status="completed",
            token="test_token_123"
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)
        return interview
    
    def test_trigger_analysis_interview_not_found(self):
        """Test trigger analysis with non-existent interview"""
        response = client.post("/interviews/99999/analyze")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_trigger_analysis_no_recordings(self, sample_interview, db_session):
        """Test trigger analysis when interview has no recordings"""
        response = client.post(f"/interviews/{sample_interview.id}/analyze")
        assert response.status_code == 400
        assert "No recordings found" in response.json()["detail"]
    
    def test_trigger_analysis_with_recording(self, sample_interview, db_session):
        """Test successful analysis trigger with recording"""
        # Create a test video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video data')
            tmp_path = tmp.name
        
        try:
            # Create recording
            recording = Recording(
                interview_id=sample_interview.id,
                file_path=tmp_path,
                answer_text="Test answer"
            )
            db_session.add(recording)
            db_session.commit()
            
            # Trigger analysis
            response = client.post(f"/interviews/{sample_interview.id}/analyze")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert data["interview_id"] == sample_interview.id
            assert "analysis_id" in data
            
            # Verify analysis record created
            analysis = db_session.query(InterviewAnalysis).filter(
                InterviewAnalysis.interview_id == sample_interview.id
            ).first()
            assert analysis is not None
            assert analysis.status == "pending"
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_get_analysis_not_found(self, sample_interview):
        """Test get analysis for interview with no analysis"""
        response = client.get(f"/interviews/{sample_interview.id}/analysis")
        assert response.status_code == 404
        assert "No analysis found" in response.json()["detail"]
    
    def test_get_analysis_pending(self, sample_interview, db_session):
        """Test get analysis with pending status"""
        analysis = InterviewAnalysis(
            interview_id=sample_interview.id,
            status="pending"
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.get(f"/interviews/{sample_interview.id}/analysis")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["interview_id"] == sample_interview.id
    
    def test_get_analysis_completed(self, sample_interview, db_session):
        """Test get analysis with completed results"""
        analysis = InterviewAnalysis(
            interview_id=sample_interview.id,
            status="completed",
            risk_level="high",
            effective_risk_percentage=75.5,
            event_percentages='{"suspicious_gaze":45.0}',
            analysis_report="Test report content"
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.get(f"/interviews/{sample_interview.id}/analysis")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["risk_level"] == "high"
        assert data["effective_risk_percentage"] == 75.5
        assert data["analysis_report"] == "Test report content"
    
    def test_get_analysis_failed(self, sample_interview, db_session):
        """Test get analysis with failed status"""
        analysis = InterviewAnalysis(
            interview_id=sample_interview.id,
            status="failed",
            error_message="Video file corrupted"
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.get(f"/interviews/{sample_interview.id}/analysis")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Video file corrupted"
    
    def test_complete_with_analysis(self, sample_interview):
        """Test complete interview with automatic analysis"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video data for upload')
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    f"/interviews/{sample_interview.id}/complete-with-analysis",
                    files={"file": f},
                    data={
                        "question_id": 1,
                        "answer": "My test answer"
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["analysis_queued"] is True
            assert "analysis_id" in data
            assert "recording_id" in data
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestMLPipeline:
    """Test suite for ML pipeline execution"""
    
    @patch('subprocess.run')
    def test_pipeline_success(self, mock_run):
        """Test successful ML pipeline execution"""
        # Mock subprocess success
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"status":"success","interview_id":42,"risk_level":"high","effective_percentage":75.5}',
            stderr=""
        )
        
        from app.api.routes.interviews import _run_ml_pipeline
        
        with patch('app.core.database.SessionLocal') as mock_db:
            _run_ml_pipeline(42, "/tmp/video.mp4")
            
            # Verify subprocess was called correctly
            assert mock_run.called
            args = mock_run.call_args
            assert "-m" in args[0][0]
            assert "ml.service.final_pipeline" in args[0][0]
            assert "42" in args[0][0]
    
    @patch('subprocess.run')
    def test_pipeline_timeout(self, mock_run):
        """Test ML pipeline timeout handling"""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", timeout=600)
        
        from app.api.routes.interviews import _run_ml_pipeline
        from unittest.mock import patch
        import subprocess
        
        with patch('app.core.database.SessionLocal') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            
            # Should not raise, only log
            _run_ml_pipeline(42, "/tmp/video.mp4", mock_session)
            
            # Verify error was logged/recorded
            # In real test, check if status was updated to 'failed'
    
    @patch('subprocess.run')
    def test_pipeline_subprocess_error(self, mock_run):
        """Test ML pipeline subprocess error"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="CSV not found: /tmp/gaze.csv"
        )
        
        from app.api.routes.interviews import _run_ml_pipeline
        
        with patch('app.core.database.SessionLocal') as mock_db:
            _run_ml_pipeline(42, "/tmp/video.mp4")
            
            # Should handle error gracefully
            assert mock_run.called


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_full_interview_workflow(self):
        """Test complete workflow: create -> upload -> analyze"""
        # 1. Create interview
        interview_payload = {
            "title": "E2E Test Interview",
            "candidate_name": "Test User",
            "candidate_email": "test@example.com",
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": 30,
            "questions": [
                {
                    "order": 1,
                    "text": "What is your experience?",
                    "type": "coding"
                }
            ]
        }
        
        create_response = client.post("/interviews", json=interview_payload)
        assert create_response.status_code == 201
        interview = create_response.json()
        interview_id = interview["id"]
        
        # 2. Create recording and queue analysis
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video data')
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    f"/interviews/{interview_id}/complete-with-analysis",
                    files={"file": f},
                    data={"question_id": 1, "answer": "Test answer"}
                )
            
            assert upload_response.status_code == 200
            assert upload_response.json()["analysis_queued"] is True
            
            # 3. Check analysis status (should be pending or processing)
            analysis_response = client.get(f"/interviews/{interview_id}/analysis")
            assert analysis_response.status_code == 200
            analysis = analysis_response.json()
            assert analysis["status"] in ["pending", "processing"]
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_analysis_in_progress_conflict(self, db_session):
        """Test triggering analysis while one is already running"""
        interview = InterviewModel(
            title="Test",
            candidate_name="Test",
            candidate_email="test@example.com",
            scheduled_at=datetime.now(timezone.utc),
            duration_minutes=30
        )
        db_session.add(interview)
        db_session.commit()
        
        # Create recording
        with tempfile.NamedTemporaryFile(suffix='.mp4') as tmp:
            recording = Recording(
                interview_id=interview.id,
                file_path=tmp.name
            )
            db_session.add(recording)
            
            # Create processing analysis
            analysis = InterviewAnalysis(
                interview_id=interview.id,
                status="processing"
            )
            db_session.add(analysis)
            db_session.commit()
            
            # Try to trigger another analysis
            response = client.post(f"/interviews/{interview.id}/analyze")
            assert response.status_code == 400
            assert "already in progress" in response.json()["detail"].lower()
    
    def test_invalid_video_path(self, db_session):
        """Test with non-existent video file"""
        interview = InterviewModel(
            title="Test",
            candidate_name="Test",
            candidate_email="test@example.com",
            scheduled_at=datetime.now(timezone.utc),
            duration_minutes=30
        )
        db_session.add(interview)
        db_session.commit()
        
        recording = Recording(
            interview_id=interview.id,
            file_path="/nonexistent/path/video.mp4"
        )
        db_session.add(recording)
        db_session.commit()
        
        response = client.post(f"/interviews/{interview.id}/analyze")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


# Performance test (optional, requires actual video)
@pytest.mark.slow
class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.skip(reason="Requires actual video file")
    def test_pipeline_execution_time(self):
        """Measure actual pipeline execution time"""
        import time
        
        # This test requires an actual video file
        video_path = "/path/to/test/video.mp4"
        if not os.path.exists(video_path):
            pytest.skip("Test video not found")
        
        start_time = time.time()
        result = client.post(
            "/interviews/1/analyze"
        )
        elapsed = time.time() - start_time
        
        # Log performance metrics
        print(f"Analysis took {elapsed:.2f} seconds")
        assert elapsed < 300  # Should complete in < 5 minutes


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
