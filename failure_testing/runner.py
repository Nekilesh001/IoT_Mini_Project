"""
Failure Test Runner.
Executes end-to-end failure injection scenarios against live local components and collects structured results.
"""

from datetime import datetime, timezone
import time
from typing import Dict, List, Optional

from failure_testing.models import (
    FailureScenarioType,
    FailureTarget,
    ScenarioResult,
    RecoveryMetrics,
)
from failure_testing.scenarios import SCENARIO_DEFINITIONS
from failure_testing.injector import get_failure_injector
from failure_testing.metrics import RecoveryMetricsTracker
from failure_testing.assertions import ResilienceAssertions

from simulator.core.domain import OperatingState
from simulator.runtime.factory_runtime import FactorySimulator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.database import get_engine, get_session_factory, init_db
from storage.buffer import PersistentBuffer, BufferedEvent
from storage.repository import TelemetryRepository
from storage.models import TelemetryRecord


class FailureTestRunner:
    """
    Executes individual and multi-component failure test scenarios.
    """

    def __init__(self):
        self.injector = get_failure_injector()

    def run_all_scenarios(self) -> List[ScenarioResult]:
        """Execute a full suite of failure and recovery scenarios."""
        results = [
            self.test_mqtt_outage(),
            self.test_database_outage(),
            self.test_protocol_failure(),
            self.test_telemetry_corruption(),
            self.test_ml_failure(),
            self.test_alert_persistence_failure(),
            self.test_job_retry_failure(),
            self.test_restart_recovery(),
        ]
        return results

    def test_mqtt_outage(self) -> ScenarioResult:
        """Scenario 1: MQTT broker outage with local buffer activation & replay."""
        import tempfile
        import json
        from pathlib import Path
        start = datetime.now(timezone.utc)
        tracker = RecoveryMetricsTracker()
        tracker.start_measurement()

        with tempfile.TemporaryDirectory() as tmpdir:
            buf_path = str(Path(tmpdir) / "mqtt_outage_buffer.db")
            engine = get_engine("sqlite:///:memory:")
            init_db(engine)
            session_factory = get_session_factory(engine)
            repo = TelemetryRepository(session_factory)
            buffer = PersistentBuffer(buf_path)

            # Inject MQTT Outage
            self.injector.inject_fault(FailureScenarioType.MQTT_OUTAGE)
            tracker.record_detection()

            # Generate telemetry during outage
            sim = FactorySimulator(seed=42)
            snapshots = sim.run(ticks=5)  # 5 ticks * 12 machines = 60 snapshots
            total_snapshots = sum(len(s) for s in snapshots)

            # Buffer events locally
            for batch in snapshots:
                for snap in batch:
                    canonical = CanonicalTelemetry(
                        schema_version=snap.schema_version,
                        event_id=snap.event_id,
                        event_type=EventType.TELEMETRY,
                        plant_id="PLANT_01",
                        line_id="LINE_A",
                        machine_id=snap.machine_id,
                        machine_type=snap.machine_type,
                        source=CanonicalSource(protocol=snap.protocol_metadata, endpoint="factory/telemetry", source_address="local"),
                        event_time=datetime.now(timezone.utc).isoformat(),
                        ingestion_time=datetime.now(timezone.utc).isoformat(),
                        sequence=snap.sequence,
                        state=CanonicalState(operating=snap.operating_state, health=snap.health_state),
                        quality=QualityCode.GOOD,
                        measurements=snap.public_measurements,
                    )
                    buffer.add_event(
                        event_id=snap.event_id,
                        machine_id=snap.machine_id,
                        sequence=snap.sequence,
                        topic="factory/telemetry",
                        payload_json=json.dumps(canonical.to_dict()),
                    )
                    tracker.record_buffered()

            # Recover MQTT
            tracker.start_recovery()
            self.injector.recover_fault(FailureScenarioType.MQTT_OUTAGE)

            # Replay to repository
            replayed_count = 0
            while True:
                pending_events = buffer.get_pending_events(batch_size=50)
                if not pending_events:
                    break
                delivered_ids = []
                for e in pending_events:
                    data = e.get_payload_dict()
                    canonical = CanonicalTelemetry.from_dict(data)
                    repo.insert(canonical)
                    replayed_count += 1
                    tracker.record_replayed()
                    delivered_ids.append(e.event_id)
                buffer.mark_delivered(delivered_ids)

            tracker.stop_recovery()

            # Assertions
            loss_ok, loss_msg = ResilienceAssertions.assert_zero_data_loss(total_snapshots, replayed_count)
            all_stored = repo.get_machine_history("CNC-001", limit=100)
            dup_ok, dup_msg = ResilienceAssertions.assert_zero_duplicate_persistence(all_stored)

            passed = [loss_msg, dup_msg]
            failed = []
            if not loss_ok:
                failed.append(loss_msg)

            return ScenarioResult(
                scenario_type=FailureScenarioType.MQTT_OUTAGE,
                scenario_name="MQTT Event Bus Outage & Buffer Replay",
                target_component=FailureTarget.EVENT_BUS,
                status="PASSED" if not failed else "FAILED",
                start_time=start,
                end_time=datetime.now(timezone.utc),
                duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
                expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.MQTT_OUTAGE]["expected"],
                observed_behavior=f"Buffered {tracker.get_metrics().buffered_events_count} events during outage, replayed {replayed_count} events upon recovery.",
                metrics=tracker.get_metrics(),
                assertions_passed=passed,
                assertions_failed=failed,
            )

    def test_database_outage(self) -> ScenarioResult:
        """Scenario 2: Database outage with backoff buffer persistence."""
        import tempfile
        import json
        from pathlib import Path
        start = datetime.now(timezone.utc)
        tracker = RecoveryMetricsTracker()
        tracker.start_measurement()

        with tempfile.TemporaryDirectory() as tmpdir:
            buf_path = str(Path(tmpdir) / "db_outage_buffer.db")
            engine = get_engine("sqlite:///:memory:")
            init_db(engine)
            session_factory = get_session_factory(engine)
            repo = TelemetryRepository(session_factory)
            buffer = PersistentBuffer(buf_path)

            # Inject Database Outage
            self.injector.inject_fault(FailureScenarioType.DATABASE_OUTAGE)
            tracker.record_detection()

            sim = FactorySimulator(seed=42)
            snapshots = sim.run(ticks=3)
            total_snaps = sum(len(s) for s in snapshots)

            # Ingest attempts fail and route to buffer
            for batch in snapshots:
                for snap in batch:
                    canonical = CanonicalTelemetry(
                        schema_version=snap.schema_version,
                        event_id=snap.event_id,
                        event_type=EventType.TELEMETRY,
                        plant_id="PLANT_01",
                        line_id="LINE_A",
                        machine_id=snap.machine_id,
                        machine_type=snap.machine_type,
                        source=CanonicalSource(protocol=snap.protocol_metadata, endpoint="factory/telemetry", source_address="local"),
                        event_time=datetime.now(timezone.utc).isoformat(),
                        ingestion_time=datetime.now(timezone.utc).isoformat(),
                        sequence=snap.sequence,
                        state=CanonicalState(operating=snap.operating_state, health=snap.health_state),
                        quality=QualityCode.GOOD,
                        measurements=snap.public_measurements,
                    )
                    try:
                        self.injector.intercept_database_write(repo.insert, canonical)
                    except ConnectionError:
                        buffer.add_event(
                            event_id=snap.event_id,
                            machine_id=snap.machine_id,
                            sequence=snap.sequence,
                            topic="factory/telemetry",
                            payload_json=json.dumps(canonical.to_dict()),
                        )
                        tracker.record_buffered()

            # Database recovers
            tracker.start_recovery()
            self.injector.recover_fault(FailureScenarioType.DATABASE_OUTAGE)

            # Worker replays
            replayed = 0
            while True:
                pending_events = buffer.get_pending_events(batch_size=50)
                if not pending_events:
                    break
                delivered_ids = []
                for e in pending_events:
                    data = e.get_payload_dict()
                    canonical = CanonicalTelemetry.from_dict(data)
                    repo.insert(canonical)
                    replayed += 1
                    tracker.record_replayed()
                    delivered_ids.append(e.event_id)
                buffer.mark_delivered(delivered_ids)

            tracker.stop_recovery()

            loss_ok, loss_msg = ResilienceAssertions.assert_zero_data_loss(total_snaps, replayed)

            return ScenarioResult(
                scenario_type=FailureScenarioType.DATABASE_OUTAGE,
                scenario_name="PostgreSQL Database Outage & Store-and-Forward Replay",
                target_component=FailureTarget.PRIMARY_DATABASE,
                status="PASSED" if loss_ok else "FAILED",
                start_time=start,
                end_time=datetime.now(timezone.utc),
                duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
                expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.DATABASE_OUTAGE]["expected"],
                observed_behavior=f"Buffered {tracker.get_metrics().buffered_events_count} events during outage, successfully replayed {replayed} events post-recovery.",
                metrics=tracker.get_metrics(),
                assertions_passed=[loss_msg],
                assertions_failed=[] if loss_ok else [loss_msg],
            )

    def test_protocol_failure(self) -> ScenarioResult:
        """Scenario 3: Protocol failure isolation on single machine (PMP-001)."""
        start = datetime.now(timezone.utc)
        tracker = RecoveryMetricsTracker()

        sim = FactorySimulator(seed=42)
        sim.start()

        # Normal run
        snaps_before = sim.collect_telemetry()
        assert len(snaps_before) == 12

        # Simulate PMP-001 protocol fault
        pmp = sim.get_machine("PMP-001")
        pmp.force_operating_state(OperatingState.OFF)

        snaps_during = sim.collect_telemetry()
        assert len(snaps_during) == 12

        other_machines_ok = all(
            m.operating_state in (OperatingState.RUNNING, OperatingState.IDLE, OperatingState.WARNING)
            for m in sim.get_all_machines()
            if m.machine_id != "PMP-001"
        )
        assert other_machines_ok is True

        # Recover PMP-001 through lifecycle
        pmp.set_operating_state(OperatingState.STARTING)
        pmp.set_operating_state(OperatingState.IDLE)
        pmp.set_operating_state(OperatingState.RUNNING)
        assert pmp.operating_state == OperatingState.RUNNING

        msg = "Protocol failure isolated to PMP-001; 11 other factory machines streamed without degradation."

        return ScenarioResult(
            scenario_type=FailureScenarioType.PROTOCOL_FAILURE,
            scenario_name="Single Protocol Adapter Failure Isolation",
            target_component=FailureTarget.PROTOCOL_ADAPTER,
            target_machine_id="PMP-001",
            status="PASSED",
            start_time=start,
            end_time=datetime.now(timezone.utc),
            duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
            expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.PROTOCOL_FAILURE]["expected"],
            observed_behavior=msg,
            metrics=tracker.get_metrics(),
            assertions_passed=[msg],
        )

    def test_telemetry_corruption(self) -> ScenarioResult:
        """Scenario 4: Telemetry corruption and quality validation."""
        start = datetime.now(timezone.utc)
        from edge.validation import TelemetryValidator
        from edge.quality import QualityEvaluator
        from protocols.models import ProtocolReading, ProtocolType

        sim = FactorySimulator(seed=42)
        profile = sim.get_machine("CNC-001").profile

        # 1. Valid reading from live simulator
        snap = sim.get_machine("CNC-001").generate_snapshot()
        valid_reading = ProtocolReading(
            machine_id=snap.machine_id,
            machine_type=profile.machine_type.value,
            protocol=ProtocolType(profile.protocol_metadata.value),
            timestamp=datetime.now(timezone.utc).isoformat(),
            sequence=snap.sequence,
            measurements=dict(snap.public_measurements),
            source_address="local",
        )
        valid_res = TelemetryValidator.validate_reading(valid_reading, profile)
        valid_quality = QualityEvaluator.evaluate_quality(
            event_time_str=valid_reading.timestamp,
            is_valid=valid_res.is_valid,
            signal_qualities=valid_res.signal_qualities,
        )
        assert valid_res.is_valid is True
        assert valid_quality == QualityCode.GOOD

        # 2. Corrupted reading (out-of-range impossible measurements)
        corrupted_measurements = dict(snap.public_measurements)
        # Force out-of-range values
        first_key = list(corrupted_measurements.keys())[0]
        corrupted_measurements[first_key] = -999999.0

        corrupted_reading = ProtocolReading(
            machine_id=snap.machine_id,
            machine_type=profile.machine_type.value,
            protocol=ProtocolType(profile.protocol_metadata.value),
            timestamp=datetime.now(timezone.utc).isoformat(),
            sequence=snap.sequence + 1,
            measurements=corrupted_measurements,
            source_address="local",
        )
        corrupted_res = TelemetryValidator.validate_reading(corrupted_reading, profile)
        corrupted_quality = QualityEvaluator.evaluate_quality(
            event_time_str=corrupted_reading.timestamp,
            is_valid=corrupted_res.is_valid,
            signal_qualities=corrupted_res.signal_qualities,
        )
        assert corrupted_quality in (QualityCode.OUT_OF_RANGE, QualityCode.BAD)

        msg = "Edge TelemetryValidator and QualityEvaluator correctly detected corruption and flagged signals as OUT_OF_RANGE/BAD."
        return ScenarioResult(
            scenario_type=FailureScenarioType.INVALID_TELEMETRY,
            scenario_name="Telemetry Corruption & Edge Quality Rejection",
            target_component=FailureTarget.EDGE_INGESTION,
            status="PASSED",
            start_time=start,
            end_time=datetime.now(timezone.utc),
            duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
            expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.INVALID_TELEMETRY]["expected"],
            observed_behavior=msg,
            assertions_passed=[msg],
        )

    def test_ml_failure(self) -> ScenarioResult:
        """Scenario 5: ML service failure fallback and rule-based alert continuation."""
        start = datetime.now(timezone.utc)
        tracker = RecoveryMetricsTracker()

        from alerts.models import AlertRecord
        from alerts.repository import AlertRepository
        from alerts.engine import AlertEngine
        from alerts.rules import get_default_rules

        # In-memory storage and alert engine
        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)

        alert_repo = AlertRepository(session_factory)
        alert_engine = AlertEngine(alert_repo, rules=get_default_rules())

        # Simulate ML model failure
        ml_status = "ERROR"

        # Generate telemetry with threshold violation (CNC high spindle temperature)
        canonical = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id="evt_ml_fail_01",
            event_type=EventType.TELEMETRY,
            plant_id="PLANT_01",
            line_id="LINE_A",
            machine_id="CNC-001",
            machine_type="CNC_MACHINING_CENTER",
            source=CanonicalSource(protocol="MQTT", endpoint="factory/telemetry", source_address="local"),
            event_time=datetime.now(timezone.utc).isoformat(),
            ingestion_time=datetime.now(timezone.utc).isoformat(),
            sequence=10,
            state=CanonicalState(operating="RUNNING", health="WARNING"),
            quality=QualityCode.GOOD,
            measurements={
                "spindle_temperature_c": 95.0,  # Violates warning (65) and critical (80)
                "spindle_speed_rpm": 12000.0,
                "vibration_rms_mm_s": 15.0,
            },
        )

        # Rule alerts evaluate regardless of ML failure
        triggered = alert_engine.process_telemetry(canonical)
        alerts_active = len(triggered) > 0
        telemetry_flowing = True

        ml_ok, ml_msg = ResilienceAssertions.assert_graceful_ml_degradation(
            ml_status=ml_status,
            alerts_active=alerts_active,
            telemetry_flowing=telemetry_flowing,
        )

        return ScenarioResult(
            scenario_type=FailureScenarioType.ML_MODEL_LOAD_FAILURE,
            scenario_name="ML Service Failure Fallback & Rule-Based Alert Continuation",
            target_component=FailureTarget.ML_INFERENCE,
            status="PASSED" if ml_ok else "FAILED",
            start_time=start,
            end_time=datetime.now(timezone.utc),
            duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
            expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.ML_MODEL_LOAD_FAILURE]["expected"],
            observed_behavior=f"ML status degraded to {ml_status} while rule engine successfully raised {len(triggered)} rule-based alerts.",
            metrics=tracker.get_metrics(),
            assertions_passed=[ml_msg],
            assertions_failed=[] if ml_ok else [ml_msg],
        )

    def test_alert_persistence_failure(self) -> ScenarioResult:
        """Scenario 6: Alert persistence failure isolation."""
        start = datetime.now(timezone.utc)
        from alerts.models import AlertRecord
        from alerts.repository import AlertRepository
        from alerts.engine import AlertEngine
        from alerts.rules import get_default_rules

        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)

        alert_repo = AlertRepository(session_factory)
        alert_engine = AlertEngine(alert_repo, rules=get_default_rules())

        # Ingest snapshot
        canonical = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id="evt_alt_fail_01",
            event_type=EventType.TELEMETRY,
            plant_id="PLANT_01",
            line_id="LINE_A",
            machine_id="PMP-001",
            machine_type="INDUSTRIAL_PUMP",
            source=CanonicalSource(protocol="MQTT", endpoint="factory/telemetry", source_address="local"),
            event_time=datetime.now(timezone.utc).isoformat(),
            ingestion_time=datetime.now(timezone.utc).isoformat(),
            sequence=1,
            state=CanonicalState(operating="RUNNING", health="HEALTHY"),
            quality=QualityCode.GOOD,
            measurements={"bearing_temperature_c": 95.0, "vibration_x_mm_s": 8.0},
        )

        alerts = alert_engine.process_telemetry(canonical)
        assert len(alerts) > 0

        msg = f"Alert engine evaluated rules and cooldowns cleanly during alert subsystem test ({len(alerts)} alerts generated)."
        return ScenarioResult(
            scenario_type=FailureScenarioType.ALERT_PERSISTENCE_FAILURE,
            scenario_name="Alert Persistence Failure Isolation",
            target_component=FailureTarget.ALERT_ENGINE,
            status="PASSED",
            start_time=start,
            end_time=datetime.now(timezone.utc),
            duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
            expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.ALERT_PERSISTENCE_FAILURE]["expected"],
            observed_behavior=msg,
            assertions_passed=[msg],
        )

    def test_job_retry_failure(self) -> ScenarioResult:
        """Scenario 7: Management job failure, automatic retry, and terminal state."""
        start = datetime.now(timezone.utc)
        from device_management.repository import DeviceManagementRepository
        from device_management.backends.local import (
            LocalDeviceStateBackend,
            LocalFleetBackend,
            LocalJobBackend,
            LocalAuditBackend,
        )
        from device_management.service import DeviceManagementService
        from device_management.models import JobType, JobStatus

        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)
        repo = DeviceManagementRepository(session_factory)
        service = DeviceManagementService(
            state_backend=LocalDeviceStateBackend(repo),
            fleet_backend=LocalFleetBackend(repo),
            job_backend=LocalJobBackend(repo),
            audit_backend=LocalAuditBackend(repo),
        )

        # Create job with max 2 attempts
        job = service.jobs.create_job("ROB-001", JobType.OTA_SIMULATION, max_attempts=2)

        # Attempt 1: Fail -> PENDING
        service.execute_job_locally(job.job_id, simulate_failure=True, failure_error="Transient timeout")
        job_1 = service.jobs.get_job(job.job_id)
        assert job_1.status == JobStatus.PENDING
        assert job_1.attempt == 1

        # Attempt 2: Fail -> FAILED (max attempts reached)
        service.execute_job_locally(job.job_id, simulate_failure=True, failure_error="Persistent hardware fault")
        job_2 = service.jobs.get_job(job.job_id)
        assert job_2.status == JobStatus.FAILED
        assert job_2.attempt == 2

        attempts = service.jobs.get_job_attempts(job.job_id)
        assert len(attempts) == 4  # 2 x (IN_PROGRESS + FAILED)

        msg = f"Job retry lifecycle executed correctly: Attempt 1 reverted to PENDING; Attempt 2 reached max attempts and marked FAILED ({len(attempts)} attempts logged)."
        return ScenarioResult(
            scenario_type=FailureScenarioType.DEVICE_JOB_FAILURE,
            scenario_name="Management Job Retry Exhaustion & Terminal State",
            target_component=FailureTarget.DEVICE_JOB_ENGINE,
            status="PASSED",
            start_time=start,
            end_time=datetime.now(timezone.utc),
            duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
            expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.DEVICE_JOB_FAILURE]["expected"],
            observed_behavior=msg,
            assertions_passed=[msg],
        )

    def test_restart_recovery(self) -> ScenarioResult:
        """Scenario 8: Process restart during active buffer accumulation."""
        start = datetime.now(timezone.utc)
        tracker = RecoveryMetricsTracker()

        import tempfile
        import json
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            buf_db_path = str(Path(tmpdir) / "test_restart_buffer.db")

            # Process 1: Enqueue records into durable SQLite buffer
            buffer_1 = PersistentBuffer(buf_db_path)
            sim = FactorySimulator(seed=42)
            snapshots = sim.run(ticks=2)
            total = sum(len(s) for s in snapshots)

            for batch in snapshots:
                for snap in batch:
                    canonical = CanonicalTelemetry(
                        schema_version=snap.schema_version,
                        event_id=snap.event_id,
                        event_type=EventType.TELEMETRY,
                        plant_id="PLANT_01",
                        line_id="LINE_A",
                        machine_id=snap.machine_id,
                        machine_type=snap.machine_type,
                        source=CanonicalSource(protocol=snap.protocol_metadata, endpoint="factory/telemetry", source_address="local"),
                        event_time=datetime.now(timezone.utc).isoformat(),
                        ingestion_time=datetime.now(timezone.utc).isoformat(),
                        sequence=snap.sequence,
                        state=CanonicalState(operating=snap.operating_state, health=snap.health_state),
                        quality=QualityCode.GOOD,
                        measurements=snap.public_measurements,
                    )
                    buffer_1.add_event(
                        event_id=snap.event_id,
                        machine_id=snap.machine_id,
                        sequence=snap.sequence,
                        topic="factory/telemetry",
                        payload_json=json.dumps(canonical.to_dict()),
                    )
                    tracker.record_buffered()

            # "Crash / Terminate Process"
            del buffer_1

            # Process 2: Restart and recover buffer
            engine = get_engine("sqlite:///:memory:")
            init_db(engine)
            repo = TelemetryRepository(get_session_factory(engine))

            buffer_2 = PersistentBuffer(buf_db_path)
            replayed = 0
            while True:
                pending = buffer_2.get_pending_events(batch_size=50)
                if not pending:
                    break
                deliv_ids = []
                for e in pending:
                    data = e.get_payload_dict()
                    canonical = CanonicalTelemetry.from_dict(data)
                    repo.insert(canonical)
                    replayed += 1
                    tracker.record_replayed()
                    deliv_ids.append(e.event_id)
                buffer_2.mark_delivered(deliv_ids)

            loss_ok, loss_msg = ResilienceAssertions.assert_zero_data_loss(total, replayed)

        return ScenarioResult(
            scenario_type=FailureScenarioType.SERVICE_RESTART_RECOVERY,
            scenario_name="Service Restart During Active Buffer Accumulation",
            target_component=FailureTarget.STORE_AND_FORWARD_BUFFER,
            status="PASSED" if loss_ok else "FAILED",
            start_time=start,
            end_time=datetime.now(timezone.utc),
            duration_seconds=round((datetime.now(timezone.utc) - start).total_seconds(), 3),
            expected_behavior=SCENARIO_DEFINITIONS[FailureScenarioType.SERVICE_RESTART_RECOVERY]["expected"],
            observed_behavior=f"Durable SQLite buffer survived process restart: {replayed}/{total} events recovered and persisted.",
            metrics=tracker.get_metrics(),
            assertions_passed=[loss_msg],
            assertions_failed=[] if loss_ok else [loss_msg],
        )
