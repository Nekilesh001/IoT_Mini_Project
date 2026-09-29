"""
Exceptions for the Edge ML Inference subsystem.
"""


class InferenceError(Exception):
    """Base exception for all ML inference errors."""
    pass


class ModelNotFoundError(InferenceError):
    """Raised when a required model artifact or metadata JSON file cannot be found."""
    pass


class ModelLoadError(InferenceError):
    """Raised when a model binary fails to deserialize or load into memory."""
    pass


class ModelSchemaMismatchError(InferenceError):
    """Raised when model metadata does not agree with the model artifact or feature schema."""
    pass


class FeatureSchemaMismatchError(InferenceError):
    """Raised when runtime features do not match the expected count, names, or ordering."""
    pass


class InsufficientHistoryError(InferenceError):
    """Raised when a temporal feature buffer does not yet contain enough samples for inference."""
    pass


class TargetLeakageError(InferenceError):
    """Raised when a prohibited target, ground-truth, or simulated label column is detected in features."""
    pass


class InvalidTelemetryError(InferenceError):
    """Raised when incoming telemetry is malformed, has invalid quality, or lacks required fields."""
    pass
