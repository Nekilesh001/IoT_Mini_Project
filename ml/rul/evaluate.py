"""
Evaluation metrics and report generation for Remaining Useful Life (RUL) models.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    median_absolute_error,
)


def evaluate_rul_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    baseline_pred: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Computes regression evaluation metrics for RUL predictions.
    """
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    medae = float(median_absolute_error(y_true, y_pred))

    metrics: Dict[str, Any] = {
        "num_samples": len(y_true),
        "mean_absolute_error_seconds": round(mae, 2),
        "root_mean_squared_error_seconds": round(rmse, 2),
        "r2_score": round(r2, 4),
        "median_absolute_error_seconds": round(medae, 2),
        "target_mean_seconds": round(float(np.mean(y_true)), 2),
        "target_std_seconds": round(float(np.std(y_true)), 2),
    }

    if baseline_pred is not None and len(baseline_pred) == len(y_true):
        base_mae = float(mean_absolute_error(y_true, baseline_pred))
        base_rmse = float(np.sqrt(mean_squared_error(y_true, baseline_pred)))
        base_r2 = float(r2_score(y_true, baseline_pred))
        metrics["baseline_mae_seconds"] = round(base_mae, 2)
        metrics["baseline_rmse_seconds"] = round(base_rmse, 2)
        metrics["baseline_r2"] = round(base_r2, 4)
        metrics["mae_improvement_pct"] = round(
            float((base_mae - mae) / base_mae * 100.0) if base_mae > 0 else 0.0, 2
        )

    return metrics
