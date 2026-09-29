"""
Repository for persisting and querying Fault Scenario states.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import sessionmaker

from scenarios.models import ScenarioStateRecord


class ScenarioStateRepository:
    """
    Database repository providing process-safe scenario state synchronization.
    """

    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory

    def get_state(self, scenario_id: str) -> Optional[ScenarioStateRecord]:
        with self._session_factory() as session:
            return session.query(ScenarioStateRecord).filter(
                ScenarioStateRecord.scenario_id == scenario_id
            ).first()

    def get_active_scenarios(self) -> List[str]:
        """Returns list of active scenario IDs."""
        with self._session_factory() as session:
            records = session.query(ScenarioStateRecord).filter(
                ScenarioStateRecord.state == "ACTIVE"
            ).all()
            return [r.scenario_id for r in records]

    def get_all_states(self) -> Dict[str, ScenarioStateRecord]:
        with self._session_factory() as session:
            records = session.query(ScenarioStateRecord).all()
            return {r.scenario_id: r for r in records}

    def set_state(self, scenario_id: str, machine_id: str, state: str, elapsed_seconds: float = 0.0) -> ScenarioStateRecord:
        with self._session_factory() as session:
            record = session.query(ScenarioStateRecord).filter(
                ScenarioStateRecord.scenario_id == scenario_id
            ).first()
            now = datetime.now(timezone.utc)
            if not record:
                record = ScenarioStateRecord(
                    scenario_id=scenario_id,
                    machine_id=machine_id,
                    state=state,
                    elapsed_seconds=elapsed_seconds,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.machine_id = machine_id
                record.state = state
                record.elapsed_seconds = elapsed_seconds
                record.updated_at = now
            session.commit()
            session.refresh(record)
            return record
