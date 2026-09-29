"""
Evaluation metrics and report generation for Anomaly Detection models.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
)


def evaluate_anomaly_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray,
) -> Dict[str, Any]:
    """
    Computes classification and ranking metrics against offline ground-truth labels.
    """
    total = len(y_true)
    anomaly_count = int(np.sum(y_pred))
    anomaly_rate = float(anomaly_count / total) if total > 0 else 0.0

    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    roc_auc = None
    pr_auc = None
    if len(np.unique(y_true)) > 1:
        try:
            roc_auc = float(roc_auc_score(y_true, scores))
            pr_auc = float(average_precision_score(y_true, scores))
        except Exception:
            pass

    return {
        "total_samples": total,
        "predicted_anomalies": anomaly_count,
        "predicted_anomaly_rate": round(anomaly_rate, 4),
        "ground_truth_anomalies": int(np.sum(y_true)),
        "ground_truth_anomaly_rate": round(float(np.mean(y_true)), 4) if total > 0 else 0.0,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
    }
