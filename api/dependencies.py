"""
FastAPI Dependencies & Shared Services.
"""

from functools import lru_cache
from typing import Dict
from api.config import APIConfig
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from simulator.runtime.factory_runtime import FactorySimulator
from simulator.core.domain import MachineProfile


@lru_cache()
def get_api_config() -> APIConfig:
    return APIConfig()


_engine = None
_session_factory = None
_factory_profiles = None


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


def get_factory_profiles() -> Dict[str, MachineProfile]:
    global _factory_profiles
    if _factory_profiles is None:
        sim = FactorySimulator(seed=42)
        _factory_profiles = {m.machine_id: m.profile for m in sim.get_all_machines()}
    return _factory_profiles
