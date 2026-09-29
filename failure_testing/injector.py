"""
Deterministic Failure Injector.
Provides fault injection hooks for Event Bus, Database, Protocol Adapters, Edge Quality, ML Inference, and Alert Engine.
"""

from contextlib import contextmanager
import logging
from typing import Any, Callable, Dict, Generator, Optional, Set
import time

from failure_testing.models import FailureScenarioType, FailureTarget

logger = logging.getLogger("failure_testing.injector")


class FailureInjector:
    """
    Coordinates active failure simulations across the system.
    """

    def __init__(self):
        self._active_faults: Set[FailureScenarioType] = set()
        self._fault_params: Dict[FailureScenarioType, Dict[str, Any]] = {}

    def is_fault_active(self, scenario_type: FailureScenarioType) -> bool:
        return scenario_type in self._active_faults

    def inject_fault(self, scenario_type: FailureScenarioType, params: Optional[Dict[str, Any]] = None) -> None:
        """Activate a simulated failure mode."""
        self._active_faults.add(scenario_type)
        self._fault_params[scenario_type] = params or {}
        logger.warning(f"[FailureInjector] Fault ACTIVATED: {scenario_type.value} (params={params})")

    def recover_fault(self, scenario_type: FailureScenarioType) -> None:
        """Deactivate a simulated failure mode."""
        self._active_faults.discard(scenario_type)
        self._fault_params.pop(scenario_type, None)
        logger.info(f"[FailureInjector] Fault RECOVERED: {scenario_type.value}")

    def clear_all_faults(self) -> None:
        """Clear all active failure injections."""
        self._active_faults.clear()
        self._fault_params.clear()

    @contextmanager
    def scoped_fault(self, scenario_type: FailureScenarioType, params: Optional[Dict[str, Any]] = None) -> Generator[None, None, None]:
        """Context manager to activate a fault and ensure automatic cleanup."""
        self.inject_fault(scenario_type, params)
        try:
            yield
        finally:
            self.recover_fault(scenario_type)

    # -------------------------------------------------------------------------
    # Fault Interception Helpers
    # -------------------------------------------------------------------------
    def intercept_database_write(self, write_func: Callable, *args, **kwargs) -> Any:
        """Intercept database writes when DATABASE_OUTAGE is active."""
        if self.is_fault_active(FailureScenarioType.DATABASE_OUTAGE):
            raise ConnectionError("Simulated Database Connection Failure: PostgreSQL node unavailable.")
        return write_func(*args, **kwargs)

    def intercept_mqtt_publish(self, publish_func: Callable, *args, **kwargs) -> Any:
        """Intercept MQTT publish when MQTT_OUTAGE is active."""
        if self.is_fault_active(FailureScenarioType.MQTT_OUTAGE):
            raise ConnectionError("Simulated MQTT Broker Failure: Connection refused on port 1883.")
        return publish_func(*args, **kwargs)

    def intercept_ml_inference(self, infer_func: Callable, *args, **kwargs) -> Any:
        """Intercept ML inference when ML_INFERENCE_FAILURE is active."""
        if self.is_fault_active(FailureScenarioType.ML_INFERENCE_FAILURE):
            raise RuntimeError("Simulated ML Inference Failure: ONNX Runtime kernel execution error.")
        return infer_func(*args, **kwargs)

    def intercept_alert_persistence(self, alert_func: Callable, *args, **kwargs) -> Any:
        """Intercept alert repository operations when ALERT_PERSISTENCE_FAILURE is active."""
        if self.is_fault_active(FailureScenarioType.ALERT_PERSISTENCE_FAILURE):
            raise RuntimeError("Simulated Alert Persistence Failure: alert_records disk write lock.")
        return alert_func(*args, **kwargs)


_global_injector: Optional[FailureInjector] = None


def get_failure_injector() -> FailureInjector:
    global _global_injector
    if _global_injector is None:
        _global_injector = FailureInjector()
    return _global_injector
