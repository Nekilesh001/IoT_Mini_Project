# Reproducibility & Local Execution Guide

## 1. Running the ML Inference Demo

Execute the standalone Phase 8 demo offline:

```bash
python -m ml.inference.demo
```

This runs:
1. Model loader and metadata contract validation.
2. ONNX export and numerical tolerance verification.
3. Live streaming telemetry across CNC, Robot, Press, and Pump machines.
4. Temporal feature buffering and warm-up transitions (`NOT_READY` -> `READY`).
5. Real-time Anomaly Detection and RUL scoring.
6. Storage persistence into SQLite / PostgreSQL `ml_inferences`.
7. Operational alert integration through `MLAlertAdapter`.
8. Graceful error handling verification on malformed telemetry.

## 2. Running the Full Automated Test Suite

```bash
pytest -q
```
Expected output: `137 passed`.

## 3. Running the Dashboard & Ingestion Worker

Start the continuous worker with ML enabled:
```bash
python -m storage.worker
```

Start the FastAPI server:
```bash
uvicorn api.main:app --reload --port 8000
```

Start the React dashboard:
```bash
cd dashboard/react-app
npm run dev
```
Navigate to `http://localhost:5173/ml` to inspect the live ML console.
