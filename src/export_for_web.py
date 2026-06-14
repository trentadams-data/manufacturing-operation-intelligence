"""Assemble the combined, frontend-friendly case-study export.

Each analytics module writes its own per-domain JSON into ``data/web_exports``.
This module reads those domain files and composes a single
``manufacturing_case_study.json`` shaped for direct consumption by the React /
Vite portfolio site: a project header, headline KPI cards, a dataset profile,
each analytics domain, a root-cause list, prioritised recommendations, and a
list of chart assets with web paths.

Run order: this step assumes the analytics modules have already run (their
domain JSON files exist). ``src/run_pipeline.py`` guarantees that ordering.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import MACHINE_SPECS, PLANTS, PRODUCTS, SHIFTS, WEB_EXPORT_DIR
from src.data_io import (
    CHARTS_DIR,
    PipelineError,
    ensure_output_dirs,
    load_table,
    write_json,
)

# Run date is sourced from the data, not the wall clock, so the export is fully
# reproducible from the committed CSVs.
DATA_THROUGH = "2025-06-30"

PROJECT_HEADER = {
    "title": "Manufacturing Operations Intelligence",
    "subtitle": "OEE, Downtime, Quality, and Predictive Maintenance Analytics",
    "description": (
        "An end-to-end manufacturing operations analytics case study that turns "
        "production, maintenance, quality, and sensor data into OEE, downtime, "
        "quality, SPC, and predictive-maintenance insight, with prioritised, "
        "business-ready recommendations."
    ),
    "tools": ["Python", "Pandas", "Scikit-learn", "Matplotlib", "SPC", "Machine Learning"],
    "data_type": "Synthetic manufacturing operations data",
}

# Static metadata for the five portfolio charts. Web path is where the images are
# expected to live once copied into the portfolio site's public folder.
PUBLIC_IMAGE_BASE = "/images/manufacturing"
CHART_ASSETS = [
    {
        "key": "oee_trend",
        "title": "Weekly OEE Trend",
        "file": "oee_trend.png",
        "description": "Plant OEE and its availability and quality components by week.",
    },
    {
        "key": "downtime_pareto",
        "title": "Downtime Pareto by Reason",
        "file": "downtime_pareto.png",
        "description": "Downtime minutes by reason with cumulative contribution.",
    },
    {
        "key": "defect_rate_by_line",
        "title": "Defect Rate by Production Line",
        "file": "defect_rate_by_line.png",
        "description": "Inspection defect rate compared across production lines.",
    },
    {
        "key": "spc_control_chart",
        "title": "SPC Control Chart",
        "file": "spc_control_chart.png",
        "description": "Individuals control chart for the lowest-capability process.",
    },
    {
        "key": "maintenance_risk",
        "title": "Predicted 7-Day Failure Risk by Machine",
        "file": "maintenance_risk_top_machines.png",
        "description": "Average predicted failure probability per machine.",
    },
]

_DOMAIN_FILES = {
    "kpis": "production_kpis.json",
    "oee": "oee_summary.json",
    "downtime": "downtime_summary.json",
    "quality": "defect_summary.json",
    "spc": "spc_findings.json",
    "pm": "predictive_maintenance_results.json",
    "root_cause": "root_cause_summary.json",
}


def export_summary(summary: dict[str, object], filename: str = "portfolio_summary.json") -> None:
    """Write summary data to the web export folder (notebook compatibility)."""
    WEB_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = WEB_EXPORT_DIR / filename
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Exported summary to {output_path}")


def export_table(frame: pd.DataFrame, filename: str) -> None:
    """Write a table to the web export folder (notebook compatibility)."""
    WEB_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    (WEB_EXPORT_DIR / filename).write_text(frame.to_csv(index=False), encoding="utf-8")


def _load_domain(key: str) -> dict:
    """Load a previously written per-domain JSON export."""
    path = WEB_EXPORT_DIR / _DOMAIN_FILES[key]
    if not path.exists():
        raise PipelineError(
            f"Missing domain export '{path}'. Run the analytics modules "
            "(or `python src/run_pipeline.py`) before assembling the case study."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: float, kind: str) -> str:
    """Format a numeric value into a display string for the website cards."""
    if kind == "percent":  # value is a 0-1 ratio
        return f"{value * 100:.1f}%"
    if kind == "percent_pts":  # value is already a percentage number
        return f"{value:.1f}%"
    if kind == "currency":
        return f"${value:,.0f}"
    if kind == "number":
        return f"{value:,.0f}"
    if kind == "count":
        return f"{int(value)}"
    return str(value)


def _executive_kpis(kpis: dict, oee: dict, downtime: dict, pm: dict) -> list[dict]:
    """Build the headline KPI cards consumed by the website hero/section."""
    high_risk = sum(
        1 for m in pm.get("high_risk_machines", []) if m.get("risk_tier") == "High"
    )
    cost_of_poor_quality = float(kpis["estimated_scrap_cost"]) + float(
        kpis["estimated_rework_cost"]
    )

    specs = [
        ("plant_oee", "Plant OEE", oee["plant_total"]["oee"], "percent",
         "Availability x Performance x Quality across the plant."),
        ("first_pass_yield", "First Pass Yield", kpis["first_pass_yield"], "percent",
         "Units acceptable on the first attempt."),
        ("schedule_attainment", "Schedule Attainment", kpis["schedule_attainment"], "percent",
         "Actual output against planned volume."),
        ("units_produced", "Units Produced", kpis["total_units_produced"], "number",
         "Total units produced over the analysis window."),
        ("scrap_rate", "Scrap Rate", kpis["scrap_rate"], "percent",
         "Scrapped units as a share of output."),
        ("unplanned_downtime_share", "Unplanned Downtime", downtime["unplanned_share_pct"],
         "percent_pts", "Share of all downtime that was unplanned."),
        ("cost_of_poor_quality", "Cost of Poor Quality", cost_of_poor_quality, "currency",
         "Estimated scrap and rework margin loss."),
        ("high_risk_machines", "High-Risk Machines", high_risk, "count",
         "Machines flagged high risk by the maintenance model."),
    ]
    cards = []
    for key, label, value, kind, context in specs:
        cards.append(
            {
                "key": key,
                "label": label,
                "value": value,
                "format": kind,
                "display": _fmt(float(value), kind),
                "context": context,
            }
        )
    return cards


def _dataset_profile() -> dict:
    """Summarise the source data scale and coverage for the website."""
    names = [
        "production_runs",
        "machine_events",
        "maintenance_logs",
        "quality_inspections",
        "sensor_readings",
    ]
    counts = {}
    for name in names:
        try:
            counts[name] = int(len(load_table(name)))
        except FileNotFoundError:
            counts[name] = 0

    runs = load_table("production_runs")
    lines = sorted(runs["production_line"].unique().tolist())
    date_range = {
        "start": runs["date"].min().strftime("%Y-%m-%d"),
        "end": runs["date"].max().strftime("%Y-%m-%d"),
    }
    return {
        "data_source": "synthetic",
        "data_through": DATA_THROUGH,
        "date_range": date_range,
        "plants": len(PLANTS),
        "plant_names": PLANTS,
        "production_lines": len(lines),
        "production_line_names": lines,
        "machines": len(MACHINE_SPECS),
        "products": len(PRODUCTS),
        "shifts": SHIFTS,
        "record_counts": counts,
        "note": "Dataset is synthetic and created for portfolio demonstration purposes.",
    }


def _chart_assets() -> list[dict]:
    """Return chart asset descriptors with web paths and availability flags."""
    assets = []
    for chart in CHART_ASSETS:
        assets.append(
            {
                **chart,
                "image": f"{PUBLIC_IMAGE_BASE}/{chart['file']}",
                "available": (CHARTS_DIR / chart["file"]).exists(),
            }
        )
    return assets


def _recommendations(root_cause: dict) -> list[dict]:
    """Promote the highest-priority findings into a recommendations list."""
    recommendations = []
    for finding in root_cause.get("findings", []):
        if finding.get("priority") == "High":
            recommendations.append(
                {
                    "action": finding["recommended_action"],
                    "area": finding["affected_area"],
                    "rationale": finding["finding"],
                    "priority": finding["priority"],
                }
            )
    return recommendations


def build_combined() -> dict[str, object]:
    """Assemble the combined case-study document from the domain exports."""
    ensure_output_dirs()

    kpis = _load_domain("kpis")
    oee = _load_domain("oee")
    downtime = _load_domain("downtime")
    quality = _load_domain("quality")
    spc = _load_domain("spc")
    pm = _load_domain("pm")
    root_cause = _load_domain("root_cause")

    combined = {
        "project": PROJECT_HEADER,
        "executive_kpis": _executive_kpis(kpis, oee, downtime, pm),
        "dataset_profile": _dataset_profile(),
        "oee": oee,
        "downtime": downtime,
        "quality": quality,
        "spc": spc,
        "predictive_maintenance": pm,
        "root_cause": root_cause.get("findings", []),
        "executive_recommendations": _recommendations(root_cause),
        "charts": _chart_assets(),
        "meta": {
            "schema_version": "1.0",
            "reproducible": True,
            "note": (
                "All figures are derived from reproducible synthetic data "
                "produced by the src/generate_data.py script using a fixed "
                "random seed."
            ),
        },
    }

    path = write_json(combined, "manufacturing_case_study.json")
    print(f"Combined case study written to {path}")
    return combined


def run() -> dict[str, object]:
    """Assemble and write the combined case-study export."""
    return build_combined()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
