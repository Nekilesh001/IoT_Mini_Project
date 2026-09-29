"""
Model export and metadata serialization utilities.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import sklearn

from ml.schemas import ModelMetadata, FeatureManifestEntry

logger = logging.getLogger(__name__)


def export_model_artifact(
    model: Any,
    model_name: str,
    model_type: str,
    version: str,
    feature_names: List[str],
    metrics: Dict[str, Any],
    dataset_metadata: Dict[str, Any],
    output_dir: Path,
    hyperparameters: Optional[Dict[str, Any]] = None,
    random_seed: int = 42,
) -> Tuple[Path, Path]:
    """
    Exports trained model binary using joblib and writes companion metadata.json.
    Returns: (model_file_path, metadata_file_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save model binary
    binary_path = output_dir / f"{model_name}_{version}.joblib"
    joblib.dump(model, binary_path)

    # 2. Build metadata schema
    input_schema = {name: "float64" for name in feature_names}
    meta = ModelMetadata(
        model_id=f"{model_name}-{version}",
        model_name=model_name,
        model_type=model_type,
        version=version,
        training_timestamp=datetime.now(timezone.utc).isoformat(),
        feature_names=feature_names,
        feature_count=len(feature_names),
        input_schema=input_schema,
        hyperparameters=hyperparameters or {},
        metrics={k: float(v) for k, v in metrics.items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
        dataset_metadata=dataset_metadata,
        library_versions={
            "scikit-learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        random_seed=random_seed,
    )

    metadata_path = output_dir / f"{model_name}_{version}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(meta.to_dict(), f, indent=2)

    logger.info(f"Model exported successfully to {binary_path} and metadata to {metadata_path}")
    return binary_path, metadata_path


def load_model_artifact(model_path: Path) -> Any:
    """Loads a serialized model artifact."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    return joblib.load(model_path)
