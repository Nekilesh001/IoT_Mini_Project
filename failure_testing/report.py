"""
Failure Testing Report Generator.
Formats scenario results, recovery metrics, and assertion verdicts into clean console tables and markdown summaries.
"""

from typing import List
from failure_testing.models import ScenarioResult


class FailureReportGenerator:
    """
    Generates structured failure verification reports.
    """

    @staticmethod
    def format_console_table(results: List[ScenarioResult]) -> str:
        lines = []
        lines.append("-" * 75)
        lines.append(f"{'Scenario':<45} | {'Target':<15} | {'Result':<10}")
        lines.append("-" * 75)

        for r in results:
            lines.append(f"{r.scenario_name[:45]:<45} | {r.target_component.value[:15]:<15} | {r.status:<10}")

        lines.append("-" * 75)
        passed_count = sum(1 for r in results if r.status == "PASSED")
        total_count = len(results)
        lines.append(f"Summary: {passed_count}/{total_count} scenarios passed.")
        lines.append("-" * 75)
        return "\n".join(lines)

    @staticmethod
    def format_markdown_report(results: List[ScenarioResult]) -> str:
        lines = [
            "# Phase 12 — End-to-End Failure Testing & Verification Report",
            "",
            "**Classification**: LOCAL DEVELOPMENT FAILURE TEST",
            "",
            "| Scenario | Target Component | Status | Duration (s) | Assertions Passed |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in results:
            lines.append(
                f"| **{r.scenario_name}** | `{r.target_component.value}` | `{r.status}` | {r.duration_seconds:.3f} | {len(r.assertions_passed)} |"
            )

        lines.append("")
        lines.append("## Detailed Scenario Findings")
        for r in results:
            lines.append(f"### {r.scenario_name} (`{r.status}`)")
            lines.append(f"- **Expected Behavior**: {r.expected_behavior}")
            lines.append(f"- **Observed Behavior**: {r.observed_behavior}")
            if r.assertions_passed:
                lines.append(f"- **Passed Assertions**:")
                for a in r.assertions_passed:
                    lines.append(f"  - ✓ {a}")
            if r.assertions_failed:
                lines.append(f"- **Failed Assertions**:")
                for a in r.assertions_failed:
                    lines.append(f"  - ✗ {a}")
            lines.append("")

        return "\n".join(lines)
