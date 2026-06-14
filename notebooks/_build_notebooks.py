"""Generate lightweight, professional notebooks for the project.

Each notebook imports the project modules, explains its purpose, and shows a small
sample of output. The notebooks intentionally do not duplicate the analysis code
in ``src`` -- they call it. Run from the project root:

    python notebooks/_build_notebooks.py

This file is a build helper, not part of the analytics pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parent

BOOTSTRAP = (
    "import sys, os\n"
    "sys.path.insert(0, os.path.abspath('..'))  # make the project root importable"
)


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS = {
    "01_data_generation.ipynb": notebook([
        md(
            "# Data Generation and Validation\n\n"
            "This notebook is the starting point for the synthetic manufacturing "
            "dataset. It regenerates the processed CSVs (deterministically, via a "
            "fixed seed in `src/config.py`) and previews one table. The generation "
            "logic lives in `src/generate_data.py`."
        ),
        code(BOOTSTRAP),
        code(
            "from src import generate_data\n"
            "from src.data_io import load_table\n\n"
            "generate_data.write_processed_tables()"
        ),
        md("Preview the production runs that downstream analysis is built on:"),
        code("load_table('production_runs').head()"),
    ]),
    "02_kpi_oee_analysis.ipynb": notebook([
        md(
            "# Production KPI and OEE Analysis\n\n"
            "Loads the processed data and computes plant KPIs and OEE at multiple "
            "levels. The calculations live in `src/calculate_kpis.py` and "
            "`src/oee.py`; this notebook calls them and shows the headline results."
        ),
        code(BOOTSTRAP),
        code(
            "from src import calculate_kpis, oee\n\n"
            "kpis = calculate_kpis.run()\n"
            "oee_summary = oee.run()"
        ),
        md("Headline KPIs and plant-level OEE components:"),
        code(
            "print('First pass yield :', kpis['first_pass_yield'])\n"
            "print('Scrap rate       :', kpis['scrap_rate'])\n"
            "print('Schedule attain. :', kpis['schedule_attainment'])\n"
            "oee_summary['plant_total']"
        ),
        md("OEE by production line:"),
        code("import pandas as pd\npd.DataFrame(oee_summary['by_line'])"),
    ]),
    "03_downtime_analysis.ipynb": notebook([
        md(
            "# Downtime Pattern Analysis\n\n"
            "Classifies planned versus unplanned downtime and builds a Pareto view "
            "of the largest reasons. Logic lives in `src/downtime.py`."
        ),
        code(BOOTSTRAP),
        code("from src import downtime\n\nsummary = downtime.run()"),
        md("Pareto of downtime by reason (minutes and cumulative share):"),
        code("import pandas as pd\npd.DataFrame(summary['by_reason'])"),
    ]),
    "04_predictive_maintenance.ipynb": notebook([
        md(
            "# Predictive Maintenance Modeling\n\n"
            "Combines sensor readings, machine events, and maintenance logs into a "
            "machine-day panel, engineers a `failure_within_7_days` target, and "
            "trains two models. Logic lives in `src/predictive_maintenance.py`. "
            "Recall is the priority metric because missed failures are costly."
        ),
        code(BOOTSTRAP),
        code("from src import predictive_maintenance\n\nsummary = predictive_maintenance.run()"),
        md("Model comparison (note the recall and ROC AUC gap):"),
        code("import pandas as pd\npd.DataFrame(summary['model_results'])"),
        md("Highest-risk machines from the Random Forest:"),
        code("pd.DataFrame(summary['high_risk_machines'])[['machine_id', 'avg_risk_probability', 'risk_tier']]"),
    ]),
    "05_quality_spc_analysis.ipynb": notebook([
        md(
            "# Quality and SPC Analysis\n\n"
            "Examines defect patterns and process capability. Defect analysis lives "
            "in `src/quality.py`; control charts and Cp/Cpk live in `src/spc.py`."
        ),
        code(BOOTSTRAP),
        code(
            "from src import quality, spc\n\n"
            "quality_summary = quality.run()\n"
            "spc_summary = spc.run()"
        ),
        md("Defect rate by production line:"),
        code("import pandas as pd\npd.DataFrame(quality_summary['by_line'])"),
        md("Process capability (Cp, Cpk) by machine:"),
        code("pd.DataFrame(spc_summary['by_machine'])[['machine_id', 'cp', 'cpk', 'points_out_of_spec']]"),
    ]),
    "06_root_cause_summary.ipynb": notebook([
        md(
            "# Root Cause Summary and Web Exports\n\n"
            "Combines the findings from every domain into a business-readable "
            "root-cause table and assembles the combined case-study JSON for the "
            "website. Logic lives in `src/root_cause.py` and `src/export_for_web.py`.\n\n"
            "> Run notebooks 02-05 (or `python src/run_pipeline.py`) first so the "
            "domain exports exist."
        ),
        code(BOOTSTRAP),
        code(
            "from src import root_cause, export_for_web\n\n"
            "root_summary = root_cause.run()\n"
            "case_study = export_for_web.run()"
        ),
        md("The cross-domain root-cause findings:"),
        code(
            "import pandas as pd\n"
            "pd.DataFrame(root_summary['findings'])[['finding', 'priority', 'affected_area']]"
        ),
        md("Top-level sections available to the website:"),
        code("list(case_study.keys())"),
    ]),
}


def main() -> None:
    for name, nb in NOTEBOOKS.items():
        path = NOTEBOOKS_DIR / name
        path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
