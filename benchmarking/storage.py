"""
Storage & Buffering Benchmarks.
Measures buffer write latency, batch extraction, and replay performance.
"""

import time
import statistics
import os
from typing import Dict, Any, List

from storage.buffer import PersistentBuffer


def benchmark_buffer_operations(iterations: int = 500) -> Dict[str, Any]:
    """Benchmark persistent store-and-forward SQLite buffer insertion and retrieval."""
    db_path = "data/bench_buffer.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    try:
        buf = PersistentBuffer(db_path=db_path)

        write_latencies_us: List[float] = []

        # Warm-up
        for _ in range(20):
            buf.add_event("warm-1", "PMP-001", 1, "telemetry/pmp001", '{"v": 1}')
        buf.get_pending_events(batch_size=20)

        # Benchmark write latency
        for i in range(iterations):
            eid = f"bench-evt-{i}"
            payload = '{"vibration_rms": 2.1, "temp": 45.2, "flow": 80.0}'
            t0 = time.perf_counter()
            buf.add_event(eid, "PMP-001", i + 1, "telemetry/pmp001", payload)
            write_latencies_us.append((time.perf_counter() - t0) * 1_000_000)

        # Benchmark batch retrieval and replay
        t0_replay = time.perf_counter()
        pending = buf.get_pending_events(batch_size=iterations)
        replay_duration_ms = (time.perf_counter() - t0_replay) * 1000

        # Mark delivered
        eids = [row.event_id if hasattr(row, "event_id") else row["event_id"] for row in pending]
        t0_ack = time.perf_counter()
        buf.mark_delivered(eids)
        ack_duration_ms = (time.perf_counter() - t0_ack) * 1000

        return {
            "iterations": iterations,
            "write_mean_us": round(statistics.mean(write_latencies_us), 2),
            "write_median_us": round(statistics.median(write_latencies_us), 2),
            "write_p95_us": round(statistics.quantiles(write_latencies_us, n=20)[18], 2) if len(write_latencies_us) >= 20 else round(max(write_latencies_us), 2),
            "write_max_us": round(max(write_latencies_us), 2),
            "batch_read_ms": round(replay_duration_ms, 2),
            "batch_ack_ms": round(ack_duration_ms, 2),
            "write_throughput_msgs_sec": round(1_000_000 / statistics.mean(write_latencies_us), 2),
        }
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
