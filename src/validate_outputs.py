"""Validate that the pipeline produced a complete, well-formed set of outputs.

Checks that every expected processed CSV, output table, web JSON, and chart image
exists, that the JSON files parse, and that the combined case-study document
contains its required top-level keys. Prints a clean pass/fail summary and exits
non-zero if anything is missing or invalid.

Usage:
    python src/validate_outputs.py
    python -m src.validate_outputs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import OUTPUTS_DIR, PROCESSED_DIR, WEB_EXPORT_DIR  # noqa: E402

TABLES_DIR = OUTPUTS_DIR / "tables"
CHARTS_DIR = OUTPUTS_DIR / "charts"

PROCESSED_FILES = [
    "production_runs.csv",
    "machine_events.csv",
    "maintenance_logs.csv",
    "quality_inspections.csv",
    "sensor_readings.csv",
    "products.csv",
    "work_centers.csv",
]

OUTPUT_TABLES = [
    "production_kpi_summary.csv",
    "oee_by_line.csv",
    "oee_by_machine.csv",
    "oee_by_shift.csv",
    "oee_trend.csv",
    "downtime_by_reason.csv",
    "downtime_by_machine.csv",
    "downtime_by_line.csv",
    "defect_by_line.csv",
    "defect_by_machine.csv",
    "defect_by_shift.csv",
    "defect_types.csv",
    "spc_summary.csv",
    "spc_control_chart_data.csv",
    "predictive_maintenance_model_results.csv",
    "high_risk_machines.csv",
    "feature_importance.csv",
    "root_cause_summary.csv",
]

WEB_JSON_FILES = [
    "production_kpis.json",
    "oee_summary.json",
    "oee_trend.json",
    "downtime_summary.json",
    "downtime_pareto.json",
    "defect_summary.json",
    "spc_findings.json",
    "spc_control_chart.json",
    "predictive_maintenance_results.json",
    "high_risk_machines.json",
    "root_cause_summary.json",
    "manufacturing_case_study.json",
]

CHART_FILES = [
    "oee_trend.png",
    "downtime_pareto.png",
    "defect_rate_by_line.png",
    "spc_control_chart.png",
    "maintenance_risk_top_machines.png",
]

CASE_STUDY_KEYS = [
    "project",
    "executive_kpis",
    "dataset_profile",
    "oee",
    "downtime",
    "quality",
    "spc",
    "predictive_maintenance",
    "root_cause",
    "executive_recommendations",
    "charts",
]


class Report:
    """Accumulates pass/fail checks and prints a tidy summary."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, ok: bool, message: str) -> None:
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {message}")
        if ok:
            self.passed += 1
        else:
            self.failed += 1


def _check_files(report: Report, directory: Path, files: list[str], label: str) -> None:
    print(f"\n{label} ({directory}):")
    for name in files:
        report.check((directory / name).exists(), name)


def _check_json_valid(report: Report) -> None:
    print(f"\nJSON files parse cleanly:")
    for name in WEB_JSON_FILES:
        path = WEB_EXPORT_DIR / name
        if not path.exists():
            report.check(False, f"{name} (missing)")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            report.check(True, f"{name} (valid JSON)")
        except json.JSONDecodeError as error:
            report.check(False, f"{name} (invalid JSON: {error})")


def _check_case_study_keys(report: Report) -> None:
    print(f"\nmanufacturing_case_study.json key fields:")
    path = WEB_EXPORT_DIR / "manufacturing_case_study.json"
    if not path.exists():
        report.check(False, "manufacturing_case_study.json (missing)")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        report.check(False, f"manufacturing_case_study.json (invalid JSON: {error})")
        return

    for key in CASE_STUDY_KEYS:
        report.check(key in data, f"contains '{key}'")

    # Light structural checks on the most-consumed sections.
    report.check(
        isinstance(data.get("executive_kpis"), list) and len(data["executive_kpis"]) > 0,
        "executive_kpis is a non-empty list",
    )
    report.check(
        isinstance(data.get("root_cause"), list) and len(data["root_cause"]) > 0,
        "root_cause is a non-empty list",
    )
    report.check(
        isinstance(data.get("charts"), list) and len(data["charts"]) == len(CHART_FILES),
        f"charts lists {len(CHART_FILES)} assets",
    )


def run() -> int:
    """Run all validation checks. Returns a process exit code (0 = success)."""
    print("=" * 64)
    print("Validating Manufacturing Operations Intelligence outputs")
    print("=" * 64)

    report = Report()
    _check_files(report, PROCESSED_DIR, PROCESSED_FILES, "Processed input CSVs")
    _check_files(report, TABLES_DIR, OUTPUT_TABLES, "Output tables")
    _check_files(report, WEB_EXPORT_DIR, WEB_JSON_FILES, "Web JSON exports")
    _check_files(report, CHARTS_DIR, CHART_FILES, "Chart images")
    _check_json_valid(report)
    _check_case_study_keys(report)

    total = report.passed + report.failed
    print("\n" + "=" * 64)
    if report.failed == 0:
        print(f"RESULT: PASS - {report.passed}/{total} checks passed.")
    else:
        print(f"RESULT: FAIL - {report.failed} of {total} checks failed.")
        print("Re-run `python src/run_pipeline.py` to regenerate outputs.")
    print("=" * 64)
    return 0 if report.failed == 0 else 1


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
