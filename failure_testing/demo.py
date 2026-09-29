"""
Phase 12 Failure & Recovery Testing Demonstration Script.
Executes representative failure scenarios across MQTT, Database, Protocol, ML, Alerts, Jobs, and Restarts.
"""

import sys
from failure_testing.runner import FailureTestRunner
from failure_testing.report import FailureReportGenerator


def run_demo() -> int:
    print("=" * 75)
    print("  PHASE 12: END-TO-END FAILURE & RECOVERY TESTING DEMONSTRATION")
    print("=" * 75)

    runner = FailureTestRunner()
    results = runner.run_all_scenarios()

    print("\n" + FailureReportGenerator.format_console_table(results))

    all_passed = all(r.status == "PASSED" for r in results)
    if all_passed:
        print("\n[OK] ALL FAILURE & RECOVERY SCENARIOS PASSED (EXIT 0)\n")
        return 0
    else:
        print("\n[FAIL] SOME FAILURE SCENARIOS FAILED (EXIT 1)\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_demo())
