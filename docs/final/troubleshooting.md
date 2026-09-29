# Troubleshooting Guide — Smart Factory System

## 1. Common Operational Issues & Remediation

### Issue 1: Port Conflict (Port 8000 or 5173 Already in Use)
- **Symptom**: `OSError: [Errno 48] Address already in use` when launching FastAPI or Vite.
- **Remediation**:
  ```bash
  # Check listening ports (Windows)
  netstat -ano | findstr :8000
  # Terminate conflicting PID or change port:
  uvicorn api.main:app --port 8001
  ```

### Issue 2: PostgreSQL Storage Connection Failure
- **Symptom**: `ConnectionError: could not connect to server: Connection refused`.
- **Remediation**: The system automatically switches to local SQLite fallback (`data/telemetry_dev.db`). To force SQLite, set `DATABASE_URL=sqlite:///./data/telemetry_dev.db` in `.env`.

### Issue 3: Missing ML Model Artifacts
- **Symptom**: `FileNotFoundError: ml/anomaly/models/isolation_forest.joblib`.
- **Remediation**: Re-run the Phase 7 training pipeline to export fresh model artifacts:
  ```bash
  python -m ml.pipelines.training_pipeline
  ```

### Issue 4: 403 Forbidden on Management or Audit APIs
- **Symptom**: REST calls to `/api/security/audit` or `/api/jobs` return `403 Forbidden`.
- **Remediation**: Obtain a valid JWT access token for an authorized role (`OPERATOR`, `MAINTAINER`, or `ADMIN`) via `/api/auth/login` and pass `Authorization: Bearer <token>` in headers.

### Issue 5: React Dashboard Cannot Connect to SSE Stream
- **Symptom**: Dashboard displays "Reconnecting to telemetry stream...".
- **Remediation**: Confirm FastAPI backend is running on `http://localhost:8000` and `VITE_API_URL` is set to `http://localhost:8000` in `dashboard/react-app/.env`.

### Issue 6: Windows SQLite File Locking During Tests
- **Symptom**: `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`.
- **Remediation**: Ensure SQLite engines call `engine.dispose()` before directory cleanup, or use in-memory SQLite (`sqlite:///:memory:`).
