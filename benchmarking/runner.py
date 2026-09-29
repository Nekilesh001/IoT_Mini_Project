"""
Benchmark Suite Runner.
Executes all automated benchmarks, collects system hardware/OS environment metadata, and generates structured performance reports.
"""

import os
import sys
import platform
import psutil
from datetime import datetime, timezone
from typing import Dict, Any

from benchmarking.telemetry import benchmark_edge_normalization, benchmark_rule_alert_evaluation
from benchmarking.storage import benchmark_buffer_operations
from benchmarking.ml import benchmark_ml_pipeline
from benchmarking.api import benchmark_api_endpoints
from benchmarking.management import benchmark_device_management


class BenchmarkRunner:
    """
    Coordinates end-to-end benchmarking across all system tiers.
    """

    @staticmethod
    def get_system_environment() -> Dict[str, Any]:
        """Collect hardware, OS, and runtime environment specifications."""
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        return {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "python_version": platform.python_version(),
            "cpu": platform.processor() or "Unknown CPU",
            "cpu_cores_physical": psutil.cpu_count(logical=False) or 1,
            "cpu_cores_logical": psutil.cpu_count(logical=True) or 1,
            "total_ram_gb": ram_gb,
            "architecture": platform.machine(),
            "benchmark_classification": "LOCAL DEVELOPMENT BENCHMARK",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def run_all(self) -> Dict[str, Any]:
        """Run complete benchmark suite across all system subsystems."""
        env = self.get_system_environment()

        telemetry_bench = benchmark_edge_normalization(iterations=1000)
        rules_bench = benchmark_rule_alert_evaluation(iterations=1000)
        storage_bench = benchmark_buffer_operations(iterations=500)
        ml_bench = benchmark_ml_pipeline(iterations=200)
        api_bench = benchmark_api_endpoints(iterations=100)
        mgmt_bench = benchmark_device_management(iterations=200)

        return {
            "environment": env,
            "benchmarks": {
                "edge_normalization": telemetry_bench,
                "rule_evaluation": rules_bench,
                "storage_buffer": storage_bench,
                "ml_inference_pipeline": ml_bench,
                "api_endpoints": api_bench,
                "device_management": mgmt_bench,
            },
        }
