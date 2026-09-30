"""
FastAPI Dependencies & Shared Services.
"""

from functools import lru_cache
from typing import Dict, Optional
from api.config import APIConfig
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from simulator.runtime.factory_runtime import FactorySimulator
from simulator.core.domain import MachineProfile
from alerts.repository import AlertRepository
from alerts.engine import AlertEngine
from scenarios.manager import FaultScenarioManager
from scenarios.repository import ScenarioStateRepository


@lru_cache()
def get_api_config() -> APIConfig:
    return APIConfig()


_engine = None
_session_factory = None
_factory_profiles = None
_simulator = None
_scenario_manager = None
_alert_engine = None


def get_db_engine():
    global _engine
    if _engine is None:
        cfg = get_api_config()
        _engine = get_engine(cfg.database_url)
        init_db(_engine)
    return _engine


def get_session_factory_dep():
    global _session_factory
    if _session_factory is None:
        engine = get_db_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_telemetry_repository() -> TelemetryRepository:
    session_factory = get_session_factory_dep()
    return TelemetryRepository(session_factory)


def get_alert_repository() -> AlertRepository:
    session_factory = get_session_factory_dep()
    return AlertRepository(session_factory)


def get_alert_engine() -> AlertEngine:
    global _alert_engine
    if _alert_engine is None:
        repo = get_alert_repository()
        _alert_engine = AlertEngine(repo)
    return _alert_engine


def get_simulator_singleton() -> FactorySimulator:
    global _simulator
    if _simulator is None:
        _simulator = FactorySimulator(seed=42)
        _simulator.start()
    return _simulator


def get_fault_scenario_manager() -> FaultScenarioManager:
    global _scenario_manager
    if _scenario_manager is None:
        sim = get_simulator_singleton()
        _scenario_manager = FaultScenarioManager(factory=sim)
    return _scenario_manager


def get_scenario_repository() -> ScenarioStateRepository:
    session_factory = get_session_factory_dep()
    return ScenarioStateRepository(session_factory)


def get_factory_profiles() -> Dict[str, MachineProfile]:
    global _factory_profiles
    if _factory_profiles is None:
        sim = get_simulator_singleton()
        _factory_profiles = {m.machine_id: m.profile for m in sim.get_all_machines()}
    return _factory_profiles


def get_all_streaming_profiles() -> Dict[str, MachineProfile]:
    """Returns combined profiles for the 12 factory machines plus external IoT sensors for SSE."""
    from protocols.wokwi.registry import get_external_device_registry
    factory_profs = dict(get_factory_profiles())
    ext_registry = get_external_device_registry()
    factory_profs.update(ext_registry.get_all_machine_profiles())
    return factory_profs


_ml_service = None


def get_ml_repository():
    from storage.repository import MLInferenceRepository
    session_factory = get_session_factory_dep()
    return MLInferenceRepository(session_factory)


def get_ml_service():
    global _ml_service
    if _ml_service is None:
        from ml.inference.service import MLInferenceService
        _ml_service = MLInferenceService()
    return _ml_service


_device_mgmt_service = None


def get_device_management_repository():
    from device_management.repository import DeviceManagementRepository
    session_factory = get_session_factory_dep()
    return DeviceManagementRepository(session_factory)


def get_device_management_service():
    global _device_mgmt_service
    if _device_mgmt_service is None:
        from device_management.service import DeviceManagementService
        from device_management.backends.local import (
            LocalDeviceStateBackend,
            LocalFleetBackend,
            LocalJobBackend,
            LocalAuditBackend,
        )
        repo = get_device_management_repository()
        service = DeviceManagementService(
            state_backend=LocalDeviceStateBackend(repo),
            fleet_backend=LocalFleetBackend(repo),
            job_backend=LocalJobBackend(repo),
            audit_backend=LocalAuditBackend(repo),
        )
        # Ensure fleet is bootstrapped from profiles
        profiles = get_factory_profiles()
        service.bootstrap_fleet(profiles)
        _device_mgmt_service = service
    return _device_mgmt_service

