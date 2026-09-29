"""
Benchmark Reporting Utilities.
Generates human-readable console tables, Markdown summaries, and JSON artifacts.
"""

import json
import os
from typing import Dict, Any


def format_benchmark_console(data: Dict[str, Any]) -> str:
    """Format benchmark data into a clean console report."""
    env = data["environment"]
    b = data["benchmarks"]

    lines = [
        "=" * 75,
        "  SMART FACTORY SYSTEM BENCHMARK REPORT",
        f"  Classification: {env['benchmark_classification']}",
        "=" * 75,
        f"  OS:             {env['os']}",
        f"  Python:         {env['python_version']} ({env['architecture']})",
        f"  CPU Cores:      {env['cpu_cores_physical']} physical, {env['cpu_cores_logical']} logical",
        f"  RAM:            {env['total_ram_gb']} GB",
        f"  Timestamp:      {env['timestamp']}",
        "-" * 75,
        f"  {'Benchmark Domain':<32} | {'Mean Latency':<15} | {'Throughput / P95':<20}",
        "-" * 75,
        f"  {'Edge Telemetry Normalization':<32} | {b['edge_normalization']['mean_us']} µs/event     | {b['edge_normalization']['throughput_events_per_sec']:,.0f} events/s (p95: {b['edge_normalization']['p95_us']} µs)",
        f"  {'Rule Alert Evaluation':<32} | {b['rule_evaluation']['mean_us']} µs/eval       | {b['rule_evaluation']['throughput_evals_per_sec']:,.0f} evals/s (p95: {b['rule_evaluation']['p95_us']} µs)",
        f"  {'Persistent Buffer Insert':<32} | {b['storage_buffer']['write_mean_us']} µs/write      | {b['storage_buffer']['write_throughput_msgs_sec']:,.0f} msgs/s (p95: {b['storage_buffer']['write_p95_us']} µs)",
        f"  {'ML Feature & Inference Total':<32} | {b['ml_inference_pipeline']['total_pipeline_mean_us']} µs/infer     | {b['ml_inference_pipeline']['inferences_per_sec']:,.0f} inf/s (p95: {b['ml_inference_pipeline']['total_pipeline_p95_us']} µs)",
        f"  {'Device Shadow Delta Calc':<32} | {b['device_management']['shadow_delta_mean_us']} µs/calc      | p95: {b['device_management']['shadow_delta_p95_us']} µs",
        f"  {'Job Creation & Lifecycle':<32} | {b['device_management']['job_lifecycle_mean_us']} µs/job       | {b['device_management']['jobs_per_sec']:,.0f} jobs/s (p95: {b['device_management']['job_lifecycle_p95_us']} µs)",
        "-" * 75,
        "  FastAPI Local Endpoint Latencies (Mean / p95):",
    ]

    for path, metrics in b["api_endpoints"].items():
        lines.append(f"    - {path:<28}: {metrics['mean_ms']} ms (p95: {metrics['p95_ms']} ms)")

    lines.extend([
        "=" * 75,
        "  [OK] BENCHMARK EXECUTION COMPLETED SUCCESSFULLY",
        "=" * 75,
    ])

    return "\n".join(lines)


def save_benchmark_artifacts(data: Dict[str, Any], output_path: str = "artifacts/final/benchmark_results.json") -> None:
    """Save benchmark results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
