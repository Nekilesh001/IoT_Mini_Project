import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import mlflow
import mlflow.sklearn

logger = logging.getLogger(__name__)


class MLflowTracker:
    """
    Local file-based MLflow experiment tracker.
    Does not require any remote server, cloud credentials, or external services.
    """

    def __init__(self, tracking_uri: str = "file:./mlruns", experiment_name: str = "SmartFactory-PredictiveMaintenance"):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self._setup()

    def _setup(self) -> None:
        """Initializes local MLflow tracking URI and experiment."""
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

    def log_run(
        self,
        run_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        model: Optional[Any] = None,
        artifacts: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Executes a tracked MLflow run and logs all parameters, metrics, and models.
        Returns the active run ID.
        """
        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id

            # Log tags
            if tags:
                mlflow.set_tags(tags)

            # Log parameters (flatten or stringify nested structures)
            for k, v in parameters.items():
                if isinstance(v, (dict, list)):
                    mlflow.log_param(k, json.dumps(v))
                else:
                    mlflow.log_param(k, str(v))

            # Log numerical metrics
            for k, v in metrics.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    mlflow.log_metric(k, float(v))

            # Log raw artifact dictionaries as JSON
            if artifacts:
                for art_name, art_content in artifacts.items():
                    temp_path = Path(f"temp_{art_name}.json")
                    try:
                        with open(temp_path, "w") as f:
                            json.dump(art_content, f, indent=2)
                        mlflow.log_artifact(str(temp_path))
                    finally:
                        if temp_path.exists():
                            temp_path.unlink()

            # Log scikit-learn model object if provided
            if model is not None:
                try:
                    # If it's our wrapper, log the underlying sklearn model or the wrapper object
                    inner_model = getattr(model, "_model", model)
                    mlflow.sklearn.log_model(
                        inner_model,
                        artifact_path="model",
                        serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
                    )
                except Exception as e:
                    logger.warning(f"Could not log sklearn model directly to MLflow: {e}")

            return run_id
