# Developer Setup & Installation Guide

This runbook guides setup of the Smart Factory system on a fresh developer machine.

---

## 1. Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher (with npm)
- **Git**: 2.30+
- **PostgreSQL** (Optional — SQLite fallback is enabled by default)

---

## 2. Clone & Branch Selection
```bash
git clone https://github.com/Nekilesh001/IoT_Mini_Project.git
cd IoT_Mini_Project
git checkout dev
```

---

## 3. Python Virtual Environment Setup
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 4. Environment Configuration
```bash
# Copy example environment configuration
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Default `.env` configuration runs with local SQLite, disabled cloud connections (`AWS_ENABLED=false`), and local development security keys.

---

## 5. React Dashboard Setup
```bash
cd dashboard/react-app
npm install
npm run build
cd ../..
```

---

## 6. Verification Commands & Demos
```bash
# 1. Run full automated regression suite (235 tests)
python -m pytest -q

# 2. Run secret hygiene scanner (0 leaks expected)
python -m security.validation

# 3. Run performance benchmarks
python -m benchmarking.demo

# 4. Run authoritative 12-step final system demonstration
python -m final_demo

# 5. Run final system health verification
python -m final_verification
```

---

## 7. Starting the Live System
```bash
# Terminal 1: Start FastAPI backend with SSE streaming
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start React Operations Dashboard
cd dashboard/react-app
npm run dev
# Dashboard available at: http://localhost:5173
```
