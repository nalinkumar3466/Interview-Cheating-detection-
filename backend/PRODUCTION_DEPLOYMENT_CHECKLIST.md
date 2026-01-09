"""
PRODUCTION DEPLOYMENT CHECKLIST
ML Pipeline Integration with FastAPI

Use this checklist before deploying to production.
"""

# =============================================================================
# PRE-DEPLOYMENT CHECKLIST
# =============================================================================

CHECKLIST = """
DATABASE SETUP
  ☐ PostgreSQL running and accessible
  ☐ Database created with correct name
  ☐ Migration applied: alembic upgrade head
  ☐ interview_analysis table exists
  ☐ Backups configured and tested
  ☐ Connection pooling configured (DB_POOL_SIZE=20)

ENVIRONMENT VARIABLES
  ☐ DATABASE_URL set correctly
  ☐ FRONTEND_BASE set to production URL
  ☐ ML_PIPELINE_TIMEOUT appropriate for expected video length
  ☐ SMTP configured for email notifications (optional)
  ☐ LLM API keys configured (OpenAI/Anthropic/etc)
  ☐ LOG_LEVEL set to INFO (not DEBUG in production)

PYTHON DEPENDENCIES
  ☐ All requirements.txt packages installed
  ☐ Python version 3.9+ confirmed
  ☐ Virtual environment activated
  ☐ No conflicting package versions

ML PIPELINE
  ☐ gaze tracking model files present
  ☐ behavior analysis rules configured
  ☐ LLM prompt templates reviewed
  ☐ Temporal smoothing parameters tuned
  ☐ Test run on sample video successful

BACKEND SERVICES
  ☐ Uvicorn configured with worker processes
  ☐ Gunicorn/ASGI setup for production
  ☐ SSL/TLS certificates configured
  ☐ CORS settings correct (only allow frontend domain)
  ☐ Rate limiting configured
  ☐ Health check endpoint (/status) responding

FRONTEND
  ☐ API endpoints match backend URLs
  ☐ Analysis polling interval reasonable (10-30s)
  ☐ Error handling for all API failures
  ☐ Loading states during analysis
  ☐ Results display properly formatted

MONITORING & LOGGING
  ☐ Structured logging configured (JSON format)
  ☐ Log aggregation tool set up (ELK/Datadog/CloudWatch)
  ☐ Error tracking enabled (Sentry/Rollbar)
  ☐ Performance monitoring configured
  ☐ Database query monitoring enabled
  ☐ API response time tracking enabled

SECURITY
  ☐ API authentication enabled (if required)
  ☐ Input validation on all endpoints
  ☐ File upload size limits set
  ☐ Video file format validation
  ☐ Secrets not in version control
  ☐ Database credentials not logged
  ☐ Rate limiting to prevent abuse

TESTING
  ☐ Unit tests pass: pytest backend/tests/ -v
  ☐ Integration tests pass: pytest backend/tests/test_ml_integration.py -v
  ☐ Manual testing of full workflow completed
  ☐ Error scenarios tested (missing files, timeouts, etc)
  ☐ Load testing completed (concurrent users)
  ☐ Database performance tested with realistic data

DOCUMENTATION
  ☐ API documentation (Swagger) accessible
  ☐ Error codes documented
  ☐ Runbook created for common issues
  ☐ Team trained on new endpoints
  ☐ Troubleshooting guide prepared

BACKUP & RECOVERY
  ☐ Database backups automated
  ☐ Video files backed up or replicated
  ☐ Disaster recovery plan documented
  ☐ Recovery procedure tested

PERFORMANCE
  ☐ Video files stored efficiently (cloud storage/CDN)
  ☐ Database indexes on interview_id, status
  ☐ Connection pooling working
  ☐ Cache strategy for analysis results (optional)
  ☐ Response times < 200ms for API endpoints
  ☐ Analysis pipeline completes in < 5 minutes (95th percentile)

INFRASTRUCTURE
  ☐ Sufficient disk space for video uploads (>100GB recommended)
  ☐ Sufficient RAM for concurrent analyses (>16GB recommended)
  ☐ CPU suitable for video processing (>=4 cores)
  ☐ Network bandwidth sufficient for uploads
  ☐ Firewall rules allow DB access
  ☐ Docker/container setup tested (if applicable)
"""


# =============================================================================
# DEPLOYMENT COMMANDS
# =============================================================================

"""
1. PREPARE DATABASE
────────────────────
cd backend/
alembic upgrade head
psql -U postgres < db_init.sql  # If using SQL dumps

2. BUILD & START BACKEND
────────────────────────
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn with uvicorn workers
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using Docker
docker build -t berribot-backend -f Dockerfile .
docker run -d \
  -e DATABASE_URL=$DATABASE_URL \
  -e FRONTEND_BASE=$FRONTEND_BASE \
  -p 8000:8000 \
  -v /data/uploads:/app/backend/uploads \
  berribot-backend

3. VERIFY DEPLOYMENT
────────────────────
curl http://localhost:8000/  # Should return {"status": "ok"}
curl http://localhost:8000/interviews  # Should return interview list

4. MONITOR SERVICES
────────────────────
# Watch logs in real-time
tail -f /var/log/berribot/backend.log

# Monitor resource usage
watch -n 1 'ps aux | grep uvicorn'
df -h  # Disk space
free -h  # Memory

5. ROLLBACK PROCEDURE
──────────────────────
# If something goes wrong
git revert <commit_hash>
alembic downgrade -1  # Rollback last migration if needed
systemctl restart berribot-backend
"""


# =============================================================================
# PRODUCTION DOCKER SETUP
# =============================================================================

"""
Dockerfile:
"""

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY backend /app/backend
COPY ml /app/ml

# Create uploads directory
RUN mkdir -p /app/backend/uploads

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000


"""
docker-compose.yml (with PostgreSQL):
"""

version: '3.9'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: interview_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: interview_db
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U interview_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://interview_user:secure_password@db:5432/interview_db
      FRONTEND_BASE: http://localhost:5173
      PYTHONUNBUFFERED: 1
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/backend/uploads
      - ./events:/app/events
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  pg_data:

"""


# =============================================================================
# PRODUCTION MONITORING
# =============================================================================

"""
KEY METRICS TO MONITOR
──────────────────────

1. API Response Times
   - POST /interviews: < 500ms
   - POST /analyze: < 200ms (queue operation)
   - GET /analysis: < 200ms

2. Analysis Pipeline
   - Success rate: > 95%
   - Average duration: based on your videos
   - Error rate: < 5%
   - Timeout rate: < 1%

3. Database
   - Connection pool utilization: < 80%
   - Query execution time: < 100ms
   - Transaction conflicts: 0

4. System Resources
   - CPU usage: < 80%
   - Memory usage: < 85%
   - Disk usage: < 90%
   - Disk I/O: < 70%

5. Error Tracking
   - 500 errors: < 0.1%
   - Database errors: 0
   - Timeout errors: < 0.5%
   - LLM service errors: < 1%


ALERTING RULES
──────────────

[CRITICAL]
- API response time > 5000ms
- Database unavailable
- Disk space < 10%
- Error rate > 10%

[WARNING]
- API response time > 1000ms
- Analysis timeout rate > 5%
- Disk space < 20%
- Error rate > 5%

[INFO]
- Analysis pipeline running slow (> 10 minutes)
- High concurrent analysis requests


RECOMMENDED TOOLS
─────────────────
- Prometheus: Metrics collection
- Grafana: Metrics visualization
- ELK Stack: Log aggregation
- Sentry: Error tracking
- PagerDuty: Alerting
- DataDog: APM monitoring
- New Relic: Performance monitoring
"""


# =============================================================================
# SCALING GUIDELINES
# =============================================================================

"""
FOR SMALL DEPLOYMENTS (< 100 users)
────────────────────────────────────
- Single server: 4+ cores, 16GB RAM
- Uvicorn: 4 workers
- PostgreSQL: Local or managed service
- Storage: 100GB SSD minimum

FOR MEDIUM DEPLOYMENTS (100-1000 users)
────────────────────────────────────────
- Load balancer (nginx/HAProxy)
- 2-3 backend servers: 8+ cores, 32GB RAM each
- Uvicorn: 8 workers per server
- PostgreSQL: Managed RDS/Aurora
- Storage: S3/Cloud storage with CDN
- Redis: Optional caching layer

FOR LARGE DEPLOYMENTS (1000+ users)
────────────────────────────────────
- Kubernetes cluster (EKS/GKE/AKS)
- HPA: Auto-scale backends 5-50 replicas
- Separate ML processing cluster
- PostgreSQL: Read replicas, connection pooling (PgBouncer)
- S3/Cloud storage with CloudFront CDN
- Redis: Caching and session storage
- Message queue: RabbitMQ/SQS for pipeline jobs
- Job scheduler: Celery/APScheduler for batch processing

RESOURCE RECOMMENDATIONS BY SCALE

Videos/Day | Servers | CPU   | RAM  | Storage
────────────────────────────────────────────
10         | 1       | 4     | 16GB | 100GB
50         | 2       | 8     | 32GB | 500GB
200        | 4       | 16    | 64GB | 1TB
1000+      | 8+      | 32+   | 128+ | 5TB+

Note: Video size and complexity greatly affect requirements.
      Short, high-quality videos (1-2 min): lower end
      Long, low-quality videos (10+ min): higher end
"""


# =============================================================================
# INCIDENT RESPONSE
# =============================================================================

"""
ANALYSIS STUCK IN PROCESSING
─────────────────────────────
1. Check logs: grep "interview_42" /var/log/berribot/backend.log
2. Kill hanging process: ps aux | grep final_pipeline
3. Update status in DB: UPDATE interview_analysis SET status='failed' WHERE interview_id=42
4. Increase timeout if needed

ANALYSIS FAILURES INCREASING
────────────────────────────
1. Check LLM service status (if using external LLM)
2. Check gaze tracking model available
3. Review error_message column: SELECT error_message, COUNT(*) FROM interview_analysis WHERE status='failed' GROUP BY error_message
4. Check video quality (too dark, no face, etc)

DATABASE CONNECTION FAILURES
────────────────────────────
1. Verify PostgreSQL is running: pg_isready -h db_host
2. Check credentials in DATABASE_URL
3. Check firewall rules
4. Increase pool size if too many connections
5. Check for long-running queries: SELECT * FROM pg_stat_activity

API RESPONSE TIME DEGRADATION
──────────────────────────────
1. Check system resources: htop, iostat
2. Check database query performance: EXPLAIN ANALYZE
3. Check if analysis pipeline consuming resources
4. Scale horizontally if needed

VIDEO UPLOAD FAILURES
─────────────────────
1. Check disk space: df -h
2. Check file permissions on uploads directory
3. Check max file size limits in nginx/reverse proxy
4. Check max request body size in FastAPI configuration
"""


# =============================================================================
# POST-DEPLOYMENT VALIDATION
# =============================================================================

"""
RUN THESE TESTS AFTER DEPLOYMENT

1. Health Check
   curl http://your-domain/

2. Create Interview
   POST /interviews with test data

3. Upload and Analyze
   POST /interviews/{id}/complete-with-analysis with test video

4. Poll Results (every 10 seconds for 5 minutes)
   GET /interviews/{id}/analysis

5. Verify Database
   SELECT COUNT(*) FROM interview_analysis;
   SELECT * FROM interview_analysis WHERE status='completed' LIMIT 1;

6. Check Logs
   tail -f /var/log/berribot/backend.log

7. Load Test (optional)
   ab -n 100 -c 10 http://your-domain/interviews

8. Error Scenario Test
   - Upload corrupted video file
   - Trigger analysis with non-existent interview
   - Stop database, verify error handling
"""


print(CHECKLIST)
