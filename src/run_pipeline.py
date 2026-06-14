"""Main entry point: run the full Manufacturing Operations Intelligence pipeline.

Executes every stage in dependency order with clear progress messages and fails
cleanly with an actionable message if any stage raises an error.

Stages:
    1. Generate synthetic data
    2. Production KPIs
    3. OEE
    4. Downtime
    5. Quality and defects
    6. SPC
    7. Predictive maintenance
    8. Root-cause recommendations
    9. Combined web-ready JSON export
   10. Charts

Usage:
    python src/run_pipeline.py
    python -m src.run_pipeline
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow running as a script (``python src/run_pipeline.py``) as well as a module.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import (  # noqa: E402
    calculate_kpis,
    downtime,
    export_for_web,
    generate_data,
    make_charts,
    oee,
    predictive_maintenance,
    quality,
    root_cause,
    spc,
)
from src.data_io import PipelineError  # noqa: E402

# (label, callable) for each stage, in execution order.
STAGES = [
    ("Generate synthetic data", generate_data.write_processed_tables),
    ("Calculate production KPIs", calculate_kpis.run),
    ("Calculate OEE", oee.run),
    ("Analyze downtime", downtime.run),
    ("Analyze quality and defects", quality.run),
    ("Run SPC analysis", spc.run),
    ("Train and evaluate predictive maintenance", predictive_maintenance.run),
    ("Generate root-cause recommendations", root_cause.run),
    ("Export web-ready JSON", export_for_web.run),
    ("Generate charts", make_charts.run),
]


def run() -> int:
    """Run every stage in order. Returns a process exit code (0 = success)."""
    total = len(STAGES)
    start = time.perf_counter()
    print("=" * 64)
    print("Manufacturing Operations Intelligence - full pipeline")
    print("=" * 64)

    for index, (label, action) in enumerate(STAGES, start=1):
        print(f"\n[{index}/{total}] {label} ...")
        try:
            action()
        except FileNotFoundError as error:
            return _fail(label, error,
                         "A required input file is missing. "
                         "Run is normally self-contained; try re-running from the start.")
        except PipelineError as error:
            return _fail(label, error, "A data validation check failed.")
        except Exception as error:  # noqa: BLE001 - report any unexpected failure cleanly
            return _fail(label, error, "Unexpected error.")

    elapsed = time.perf_counter() - start
    print("\n" + "=" * 64)
    print(f"Pipeline completed successfully in {elapsed:.1f}s.")
    print("Outputs: outputs/tables, outputs/charts, data/web_exports")
    print("=" * 64)
    return 0


def _fail(stage: str, error: Exception, hint: str) -> int:
    """Print a clean failure message and return a non-zero exit code."""
    print("\n" + "!" * 64, file=sys.stderr)
    print(f"FAILED at stage: {stage}", file=sys.stderr)
    print(f"Reason: {error}", file=sys.stderr)
    print(f"Hint:   {hint}", file=sys.stderr)
    print("!" * 64, file=sys.stderr)
    return 1


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
