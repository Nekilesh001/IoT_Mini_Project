"""
Central configuration for Phase 7 Machine Learning pipelines.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List


@dataclass
class MLConfig:
    """Configuration parameters for dataset generation, feature extraction, training, and tracking."""

    # Project directories
    base_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_BASE_DIR", ".")))
    raw_data_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_RAW_DATA_DIR", "data/raw")))
    processed_data_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_PROCESSED_DATA_DIR", "data/processed")))
    features_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_FEATURES_DIR", "data/features")))
    models_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_MODELS_DIR", "data/models")))
    reports_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_REPORTS_DIR", "ml/reports")))

    # Database
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/smart_factory"))

    # Simulation dataset generation parameters
    dataset_seed: int = int(os.getenv("ML_DATASET_SEED", "42"))
    # Increased from 600 to 10000: gives ~2.8 hours of per-machine data (72,000 rows across 12 machines).
    # This provides a much more representative training set for Isolation Forest.
    num_simulation_ticks: int = int(os.getenv("ML_NUM_SIMULATION_TICKS", "10000"))
    dt_seconds: float = float(os.getenv("ML_DT_SECONDS", "1.0"))

    # Time-based splitting
    train_ratio: float = float(os.getenv("ML_TRAIN_RATIO", "0.60"))
    val_ratio: float = float(os.getenv("ML_VAL_RATIO", "0.20"))
    test_ratio: float = float(os.getenv("ML_TEST_RATIO", "0.20"))

    # Rolling window sizes (in samples / seconds)
    rolling_windows: List[int] = field(default_factory=lambda: [5, 15, 30])

    # Model parameters
    # use_dynamic_contamination=True: compute actual anomaly rate from dataset
    # rather than assuming a fixed 5% contamination regardless of fault scenario density.
    anomaly_contamination: float = float(os.getenv("ML_ANOMALY_CONTAMINATION", "0.05"))
    use_dynamic_contamination: bool = os.getenv("ML_USE_DYNAMIC_CONTAMINATION", "true").lower() in ("true", "1", "yes")
    anomaly_n_estimators: int = int(os.getenv("ML_ANOMALY_N_ESTIMATORS", "100"))
    rul_max_iter: int = int(os.getenv("ML_RUL_MAX_ITER", "150"))
    rul_learning_rate: float = float(os.getenv("ML_RUL_LEARNING_RATE", "0.05"))
    random_state: int = int(os.getenv("ML_RANDOM_STATE", "42"))

    # Tracking
    tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
    experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "SmartFactory-PredictiveMaintenance")

    def ensure_directories(self) -> None:
        """Ensures all necessary local storage directories exist."""
        for directory in [
            self.raw_data_dir,
            self.processed_data_dir,
            self.features_dir,
            self.models_dir,
            self.reports_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
