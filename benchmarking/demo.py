"""
Executable Benchmark Runner CLI.
Usage: python -m benchmarking.demo
"""

import sys
from benchmarking.runner import BenchmarkRunner
from benchmarking.report import format_benchmark_console, save_benchmark_artifacts


def main() -> int:
    try:
        runner = BenchmarkRunner()
        results = runner.run_all()
        console_report = format_benchmark_console(results)
        print(console_report)
        save_benchmark_artifacts(results)
        return 0
    except Exception as e:
        print(f"[ERROR] Benchmark failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
