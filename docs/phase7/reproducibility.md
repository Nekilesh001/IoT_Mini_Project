# Phase 7: Reproducibility Guide & Execution Commands

## 1. Prerequisites

Ensure dependencies are installed in your Python 3.11+ environment:

```bash
pip install -r requirements.txt
```

---

## 2. Running Standalone ML Pipelines

All commands run directly from the repository root:

### 1. Build Historical Dataset & Extract Features
```bash
python -m ml.pipelines.build_dataset
```
- Steps the deterministic simulator for 7200s (seed=42).
- Extracts 1,019 observable temporal features across all 12 machines.
- Saves raw and processed parquet files in `data/processed/` and `data/features/`.
- Generates `ml/reports/phase7_dataset_report.md`.

### 2. Train Unsupervised Anomaly Detection
```bash
python -m ml.pipelines.train_anomaly
```
- Fits `IsolationForest` on healthy baseline training history.
- Logs parameters, metrics, and models to local MLflow (`mlruns/`).
- Exports model binary and JSON metadata to `data/models/`.
- Generates `ml/reports/phase7_anomaly_report.md`.

### 3. Train RUL Regression Model
```bash
python -m ml.pipelines.train_rul
```
- Fits `HistGradientBoostingRegressor` and `BaselineMedianRULModel`.
- Evaluates chronological validation and test sets.
- Logs run to local MLflow (`mlruns/`).
- Exports model binary and metadata to `data/models/`.
- Generates `ml/reports/phase7_rul_report.md`.

---

## 3. Running the Comprehensive End-to-End Demo

```bash
python -m ml.demo
```
Executes the full pipeline lifecycle in sequence (Dataset Generation -> Feature Extraction -> Anti-Leakage Verification -> Chronological Split -> Model Training -> Evaluation -> MLflow Logging -> Model Export -> Reload Verification) and prints formatted summary tables.

---

## 4. Running the Automated Test Suite

```bash
pytest -q
```
Runs all 117 tests across the entire repository, including the dedicated ML test suite in `tests/ml/`.
