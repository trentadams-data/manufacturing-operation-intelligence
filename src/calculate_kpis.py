"""Manufacturing KPI calculations.

Produces a plant-level KPI summary from ``production_runs`` (joined to product
unit margins) and an estimate of margin lost to unplanned downtime. Outputs are
written as a tidy metric/value table and a web-ready JSON document.
"""

from __future__ import annotations

import pandas as pd

from src.data_io import (
    load_required,
    r,
    safe_div,
    write_json,
    write_table,
)

# Rework is recoverable, so only a fraction of the unit margin is actually lost
# when a unit is sent back for rework (handling, labour, and a small scrap share).
REWORK_MARGIN_LOSS_FRACTION = 0.30


def calculate_kpi_summary(production_runs: pd.DataFrame) -> dict[str, float]:
    """Return a concise KPI summary for the production dataset.

    Retained for backward compatibility with the analysis notebooks; the full
    reporting pipeline lives in :func:`run`.
    """
    if production_runs.empty:
        return {
            "total_units": 0.0,
            "good_units": 0.0,
            "scrap_rate": 0.0,
            "yield_rate": 0.0,
            "overall_utilization": 0.0,
        }

    total_units = production_runs["actual_units"].sum()
    good_units = production_runs["good_units"].sum()
    scrap_rate = safe_div(production_runs["scrap_units"].sum(), total_units)
    yield_rate = safe_div(good_units, total_units)
    utilization = safe_div(
        production_runs["operating_minutes"].sum(), production_runs["planned_minutes"].sum()
    )

    return {
        "total_units": r(total_units),
        "good_units": r(good_units),
        "scrap_rate": r(scrap_rate, 4),
        "yield_rate": r(yield_rate, 4),
        "overall_utilization": r(utilization, 4),
    }


def compute_kpis(
    production_runs: pd.DataFrame,
    products: pd.DataFrame,
    machine_events: pd.DataFrame,
) -> dict[str, float]:
    """Compute the full KPI dictionary used across the case study."""
    runs = production_runs.merge(
        products[["product_id", "unit_margin"]], on="product_id", how="left"
    )

    total_runs = int(len(runs))
    total_units = float(runs["actual_units"].sum())
    good_units = float(runs["good_units"].sum())
    scrap_units = float(runs["scrap_units"].sum())
    rework_units = float(runs["rework_units"].sum())
    planned_units = float(runs["planned_units"].sum())
    operating_minutes = float(runs["operating_minutes"].sum())

    scrap_rate = safe_div(scrap_units, total_units)
    rework_rate = safe_div(rework_units, total_units)
    # First pass yield: units that were good on the first attempt (neither scrapped
    # nor reworked) as a share of everything produced.
    first_pass_yield = safe_div(total_units - scrap_units - rework_units, total_units)
    throughput_per_operating_hour = safe_div(total_units, operating_minutes / 60.0)
    schedule_attainment = safe_div(total_units, planned_units)
    production_variance_units = total_units - planned_units
    production_variance_pct = safe_div(production_variance_units, planned_units)

    # Cost estimates use per-unit margin as the value of a finished unit. Scrap
    # destroys the full margin; rework recovers most of it (see constant above).
    runs["scrap_cost"] = runs["scrap_units"] * runs["unit_margin"]
    runs["rework_cost"] = runs["rework_units"] * runs["unit_margin"] * REWORK_MARGIN_LOSS_FRACTION
    estimated_scrap_cost = float(runs["scrap_cost"].sum())
    estimated_rework_cost = float(runs["rework_cost"].sum())

    # Lost margin from downtime: translate unplanned downtime minutes into forgone
    # output using the realised throughput rate, valued at the average unit margin.
    units_per_operating_minute = safe_div(total_units, operating_minutes)
    avg_unit_margin = safe_div(
        (runs["actual_units"] * runs["unit_margin"]).sum(), total_units
    )
    unplanned_downtime_minutes = 0.0
    if not machine_events.empty:
        unplanned = machine_events[machine_events["event_type"] == "unplanned"]
        unplanned_downtime_minutes = float(unplanned["downtime_minutes"].sum())
    lost_units_from_downtime = unplanned_downtime_minutes * units_per_operating_minute
    estimated_lost_margin_downtime = lost_units_from_downtime * avg_unit_margin

    return {
        "total_production_runs": total_runs,
        "total_units_produced": r(total_units),
        "total_good_units": r(good_units),
        "total_scrap_units": r(scrap_units),
        "total_rework_units": r(rework_units),
        "scrap_rate": r(scrap_rate, 4),
        "rework_rate": r(rework_rate, 4),
        "first_pass_yield": r(first_pass_yield, 4),
        "throughput_per_operating_hour": r(throughput_per_operating_hour),
        "schedule_attainment": r(schedule_attainment, 4),
        "production_variance_units": r(production_variance_units),
        "production_variance_pct": r(production_variance_pct, 4),
        "estimated_scrap_cost": r(estimated_scrap_cost),
        "estimated_rework_cost": r(estimated_rework_cost),
        "unplanned_downtime_minutes": r(unplanned_downtime_minutes),
        "estimated_lost_margin_downtime": r(estimated_lost_margin_downtime),
    }


def run() -> dict[str, float]:
    """Compute KPIs and write the table and JSON outputs."""
    production_runs = load_required(
        "production_runs",
        [
            "actual_units",
            "good_units",
            "scrap_units",
            "rework_units",
            "planned_units",
            "operating_minutes",
            "product_id",
        ],
    )
    products = load_required("products", ["product_id", "unit_margin"])
    machine_events = load_required(
        "machine_events", ["event_type", "downtime_minutes"]
    )

    kpis = compute_kpis(production_runs, products, machine_events)

    summary_table = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in kpis.items()]
    )
    write_table(summary_table, "production_kpi_summary.csv")
    write_json(kpis, "production_kpis.json")

    print("KPI summary written:")
    for key, value in kpis.items():
        print(f"  {key}: {value}")
    return kpis


def main() -> None:
    run()


if __name__ == "__main__":
    main()
