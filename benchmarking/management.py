"""
Device Management & Job Engine Benchmarks.
Measures shadow delta calculation, version conflict resolution, and job lifecycle execution latency.
"""

import time
import statistics
import tempfile
import os
from typing import Dict, Any, List

from storage.database import get_engine, get_session_factory, init_db
from device_management.repository import DeviceManagementRepository
from device_management.backends.local import LocalDeviceStateBackend, LocalJobBackend, LocalAuditBackend
from device_management.shadow import DeviceShadowManager
from device_management.jobs import JobManager
from device_management.models import JobType, JobStatus, AuditSource


def benchmark_device_management(iterations: int = 200) -> Dict[str, Any]:
    """Benchmark Device Shadow state operations and management job lifecycles."""
    engine = get_engine(database_url="sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = DeviceManagementRepository(session_factory=session_factory)

    state_backend = LocalDeviceStateBackend(repo)
    job_backend = LocalJobBackend(repo)
    audit_backend = LocalAuditBackend(repo)

    shadow_mgr = DeviceShadowManager(state_backend, audit_backend)
    job_mgr = JobManager(job_backend, audit_backend)

    # Initial shadow state
    shadow_mgr.update_reported_state("PMP-001", {"target_rpm": 1800, "valve_pos": 50})

    shadow_latencies_us: List[float] = []
    job_latencies_us: List[float] = []

    # Warm-up
    for i in range(10):
        shadow_mgr.update_desired_state("PMP-001", {"target_rpm": 1800 + i})
        job = job_mgr.create_job(
            machine_id="PMP-001",
            job_type=JobType.CONFIG_UPDATE,
            payload={"target_rpm": 1800 + i},
        )
        job_mgr.start_job(job.job_id)
        job_mgr.complete_job(job.job_id, result={"status": "OK"})

    for i in range(iterations):
        # Benchmark Shadow desired update & delta computation
        t0_sh = time.perf_counter()
        record = shadow_mgr.update_desired_state("PMP-001", {"target_rpm": 1800 + (i % 50)})
        delta = record.delta
        shadow_latencies_us.append((time.perf_counter() - t0_sh) * 1_000_000)

        # Benchmark Job creation and lifecycle execution
        t0_job = time.perf_counter()
        job = job_mgr.create_job(
            machine_id="PMP-001",
            job_type=JobType.CONFIG_UPDATE,
            payload={"target_rpm": 1800 + (i % 50)},
        )
        job_mgr.start_job(job.job_id)
        job_mgr.complete_job(job.job_id, result={"applied": True})
        job_latencies_us.append((time.perf_counter() - t0_job) * 1_000_000)

    engine.dispose()

    return {
        "iterations": iterations,
        "shadow_delta_mean_us": round(statistics.mean(shadow_latencies_us), 2),
        "shadow_delta_median_us": round(statistics.median(shadow_latencies_us), 2),
        "shadow_delta_p95_us": round(statistics.quantiles(shadow_latencies_us, n=20)[18], 2) if len(shadow_latencies_us) >= 20 else round(max(shadow_latencies_us), 2),
        "job_lifecycle_mean_us": round(statistics.mean(job_latencies_us), 2),
        "job_lifecycle_median_us": round(statistics.median(job_latencies_us), 2),
        "job_lifecycle_p95_us": round(statistics.quantiles(job_latencies_us, n=20)[18], 2) if len(job_latencies_us) >= 20 else round(max(job_latencies_us), 2),
        "job_lifecycle_max_us": round(max(job_latencies_us), 2),
        "jobs_per_sec": round(1_000_000 / statistics.mean(job_latencies_us), 2),
    }
