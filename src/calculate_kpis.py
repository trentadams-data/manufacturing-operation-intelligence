"""Utilities for KPI calculations."""

from __future__ import annotations

import pandas as pd


def calculate_kpi_summary(production_runs: pd.DataFrame) -> dict[str, float]:
    """Return a concise KPI summary for the production dataset."""
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
    scrap_rate = production_runs["scrap_units"].sum() / max(total_units, 1.0)
    yield_rate = good_units / max(total_units, 1.0)
    utilization = production_runs["operating_minutes"].sum() / max(production_runs["planned_minutes"].sum(), 1.0)

    return {
        "total_units": round(float(total_units), 2),
        "good_units": round(float(good_units), 2),
        "scrap_rate": round(float(scrap_rate), 4),
        "yield_rate": round(float(yield_rate), 4),
        "overall_utilization": round(float(utilization), 4),
    }
