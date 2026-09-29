"""
Phase 7 End-to-End Machine Learning Pipeline Demonstration.

Command: python -m ml.demo
"""

import json
import logging
from pathlib import Path
import time
import numpy as np
import pandas as pd

from ml.config import MLConfig
from ml.pipelines.build_dataset import run_build_dataset
from ml.pipelines.train_anomaly import run_train_anomaly
from ml.pipelines.train_rul import run_train_rul
from ml.export.model_export import load_model_artifact

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ml.demo")


def run_ml_demo():
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 7 — ML DATASET COLLECTION, TRAINING & MODEL EVALUATION DEMO")
    print("=" * 80)

    cfg = MLConfig(
        num_simulation_ticks=300,  # Fast and comprehensive for demo
        dataset_seed=42,
    )
    cfg.ensure_directories()

    # Step 1: Build & Process Dataset
    print("\n[Step 1/5] Collecting and Splitting Telemetry Dataset...")
    ds_metadata = run_build_dataset(cfg)
    print(f" -> Total Dataset Size: {ds_metadata.total_samples:,} records across {ds_metadata.num_machines} machines")
    print(f" -> Chronological Split: Train={ds_metadata.train_samples}, Val={ds_metadata.val_samples}, Test={ds_metadata.test_samples}")
    print(f" -> Feature Space: {ds_metadata.feature_count} features (Zero Ground-Truth Leakage)")

    # Step 2: Train & Evaluate Anomaly Detection Model
    print("\n[Step 2/5] Training Isolation Forest Anomaly Detection Model...")
    anomaly_model, anomaly_metrics = run_train_anomaly(cfg)
    print(f" -> Anomaly Model Evaluation:")
    print(f"    - F1 Score:   {anomaly_metrics['f1_score']:.4f}")
    print(f"    - Precision:  {anomaly_metrics['precision']:.4f}")
    print(f"    - Recall:     {anomaly_metrics['recall']:.4f}")
    print(f"    - ROC-AUC:    {anomaly_metrics.get('roc_auc')}")

    # Step 3: Train & Evaluate RUL Regression Model
    print("\n[Step 3/5] Training HistGradientBoosting RUL Predictive Maintenance Model...")
    rul_model, rul_metrics = run_train_rul(cfg)
    print(f" -> RUL Regression Model Evaluation:")
    print(f"    - MAE:             {rul_metrics['mean_absolute_error_seconds']} seconds")
    print(f"    - RMSE:            {rul_metrics['root_mean_squared_error_seconds']} seconds")
    print(f"    - R² Score:        {rul_metrics['r2_score']:.4f}")
    print(f"    - Baseline MAE:    {rul_metrics.get('baseline_mae_seconds')} seconds")
    print(f"    - MAE Improvement: {rul_metrics.get('mae_improvement_pct')}%")

    # Step 4: Verify Model Artifact Reload & Live Scoring
    print("\n[Step 4/5] Verifying Model Artifact Serialization and Reloading...")
    anomaly_bin = cfg.models_dir / "anomaly_isolation_forest_v1.0.0.joblib"
    rul_bin = cfg.models_dir / "rul_gradient_boosting_v1.0.0.joblib"

    reloaded_anomaly = load_model_artifact(anomaly_bin)
    reloaded_rul = load_model_artifact(rul_bin)

    test_df = pd.read_parquet(cfg.processed_data_dir / "test.parquet")
    non_feature_cols = ["machine_id", "event_time", "target_is_anomaly", "target_rul_seconds"]
    feature_cols = [c for c in test_df.columns if c not in non_feature_cols]
    sample_X = test_df[feature_cols].iloc[:5]

    sample_anom_preds = reloaded_anomaly.predict(sample_X)
    sample_rul_preds = reloaded_rul.predict(sample_X)

    print(" -> Sample Predictions on Reloaded Models (5 Test Observations):")
    for i in range(5):
        m_id = test_df["machine_id"].iloc[i]
        t_time = str(test_df["event_time"].iloc[i])
        anom = "ANOMALOUS" if sample_anom_preds[i] == 1 else "HEALTHY"
        rul_pred = sample_rul_preds[i]
        rul_true = test_df["target_rul_seconds"].iloc[i]
        print(f"    Observation {i+1} [{m_id} @ {t_time[:19]}]: Anomaly={anom} | Predicted RUL={rul_pred:.1f}s (True={rul_true:.1f}s)")

    # Step 5: Check Reports and MLflow Artifacts
    print("\n[Step 5/5] Checking Generated Evaluation Reports & Tracking Artifacts...")
    reports = list(cfg.reports_dir.glob("*.md"))
    for r in sorted(reports):
        print(f" -> Generated Report: {r.name} ({r.stat().st_size} bytes)")

    print("\n" + "=" * 80)
    print(" PHASE 7 ML PIPELINE DEMONSTRATION COMPLETE — EXIT CODE 0")
    print("=" * 80)


if __name__ == "__main__":
    run_ml_demo()
