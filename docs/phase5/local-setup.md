# Local Setup & Startup Guide — Phase 5

This guide provides instructions for running the complete local stack: PostgreSQL, Event Bus, Factory Simulation, Edge Ingestion, Storage Persistence, FastAPI backend, and React Dashboard.

---

## 1. Prerequisites

- **Python**: 3.10+ (with project virtual environment activated)
- **Node.js**: 18+ and `npm`
- **PostgreSQL**: 14+ running locally (or via Docker)
- **MQTT Broker**: Mosquitto running on port 1883 (or embedded loopback)

---

## 2. Environment Configuration

Copy the example environment file to `.env` if not already present:

```bash
cp .env.example .env
```

Ensure standard configuration values:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_factory
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
REALTIME_POLL_INTERVAL=1.0
```

---

## 3. Step-by-Step Startup Sequence

### Step 1: Start PostgreSQL & Database Schema
Ensure the database is running:
```bash
# If using Docker
docker-compose up -d postgres

# Initialize tables
python -c "from storage.database import init_db; init_db()"
```

### Step 2: Start Factory Ingestion & Persistence Pipeline
Run the background simulation and edge persistence:
```bash
# Runs simulation, protocol adapters, edge normalizer, and database writer
python -m storage.worker
```

### Step 3: Start FastAPI Backend
In a terminal window:
```bash
python -m api
```
- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- OpenAPI Specification: `http://localhost:8000/openapi.json`

### Step 4: Start React Frontend Dashboard
In another terminal window:
```bash
cd dashboard/react-app
npm install
npm run dev
```
- Dashboard URL: `http://localhost:5173`

---

## 4. One-Shot End-to-End Demo Script

To run an automated integration demo verifying data generation, edge pipeline processing, database persistence, FastAPI queries, and real-time SSE stream events in a single execution:

```bash
python -m api.demo
```

---

## 5. Running Verification Tests

```bash
# Run all Python tests (Phase 1–5)
python -m pytest -v

# Run React frontend tests
cd dashboard/react-app
npm test
```
