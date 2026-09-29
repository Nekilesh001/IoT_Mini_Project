"""
REST API Benchmarks.
Measures local HTTP request/response latency across representative FastAPI endpoints using TestClient.
"""

import time
import statistics
from typing import Dict, Any, List
from fastapi.testclient import TestClient

from api.main import create_app


def benchmark_api_endpoints(iterations: int = 20) -> Dict[str, Any]:
    """Benchmark key FastAPI REST endpoints."""
    app = create_app()
    client = TestClient(app)

    endpoints = [
        ("GET", "/api/health"),
        ("GET", "/api/machines"),
        ("GET", "/api/alerts/active"),
        ("GET", "/api/ml/status"),
        ("GET", "/api/fleet/summary"),
        ("GET", "/api/security/status"),
    ]

    results: Dict[str, Any] = {}

    # Warm-up
    for method, path in endpoints:
        client.get(path)

    for method, path in endpoints:
        latencies_ms: List[float] = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            res = client.get(path)
            latencies_ms.append((time.perf_counter() - t0) * 1000)
            assert res.status_code == 200

        results[path] = {
            "mean_ms": round(statistics.mean(latencies_ms), 2),
            "median_ms": round(statistics.median(latencies_ms), 2),
            "p95_ms": round(statistics.quantiles(latencies_ms, n=20)[18], 2) if len(latencies_ms) >= 20 else round(max(latencies_ms), 2),
            "max_ms": round(max(latencies_ms), 2),
        }

    return results
