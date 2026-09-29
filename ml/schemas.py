"""
Domain schemas and data contracts for Phase 7 ML pipelines.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TargetLeakageError(ValueError):
    """Raised when forbidden simulator ground-truth variables are detected in the feature space."""
    pass


class SignalQuality(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    MISSING = "MISSING"


@dataclass
class FeatureManifestEntry:
    """Metadata for an engineered feature in the machine learning feature manifest."""
    name: str
    source_signal: str
    machine_applicability: List[str]
    unit: str
    transformation: str
    window_samples: Optional[int]
    is_leakage_free: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_signal": self.source_signal,
            "machine_applicability": self.machine_applicability,
            "unit": self.unit,
            "transformation": self.transformation,
            "window_samples": self.window_samples,
            "is_leakage_free": self.is_leakage_free,
            "description": self.description,
        }


@dataclass
class DatasetMetadata:
    """Provenance and summary statistics for collected and processed ML datasets."""
    dataset_id: str
    source_type: str  # "POSTGRES" or "SIMULATOR"
    total_samples: int
    num_machines: int
    machine_ids: List[str]
    time_start: str
    time_end: str
    feature_count: int
    train_samples: int
    val_samples: int
    test_samples: int
    anomaly_rate: float
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_type": self.source_type,
            "total_samples": self.total_samples,
            "num_machines": self.num_machines,
            "machine_ids": self.machine_ids,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "feature_count": self.feature_count,
            "train_samples": self.train_samples,
            "val_samples": self.val_samples,
            "test_samples": self.test_samples,
            "anomaly_rate": self.anomaly_rate,
            "created_at": self.created_at,
        }


@dataclass
class ModelMetadata:
    """Artifact metadata exported alongside trained model binaries."""
    model_id: str
    model_name: str
    model_type: str  # "ISOLATION_FOREST" or "HIST_GRADIENT_BOOSTING"
    version: str
    training_timestamp: str
    feature_names: List[str]
    feature_count: int
    input_schema: Dict[str, str]
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float]
    dataset_metadata: Dict[str, Any]
    library_versions: Dict[str, str]
    random_seed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "version": self.version,
            "training_timestamp": self.training_timestamp,
            "feature_names": self.feature_names,
            "feature_count": self.feature_count,
            "input_schema": self.input_schema,
            "hyperparameters": self.hyperparameters,
            "metrics": self.metrics,
            "dataset_metadata": self.dataset_metadata,
            "library_versions": self.library_versions,
            "random_seed": self.random_seed,
        }
