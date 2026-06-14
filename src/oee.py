"""Basic OEE calculations for the analytics project."""

from __future__ import annotations

import pandas as pd


def calculate_oee(production_runs: pd.DataFrame) -> dict[str, float]:
    """Estimate OEE using availability, performance, and quality factors."""
    planned_minutes = production_runs["planned_minutes"].sum()
    operating_minutes = production_runs["operating_minutes"].sum()
    total_units = production_runs["actual_units"].sum()
    good_units = production_runs["good_units"].sum()

    availability = operating_minutes / max(planned_minutes, 1.0)
    performance = total_units / max(operating_minutes * 60.0 / 45.0, 1.0)
    quality = good_units / max(total_units, 1.0)

    oee = availability * performance * quality

    return {
        "availability": round(float(availability), 4),
        "performance": round(float(performance), 4),
        "quality": round(float(quality), 4),
        "oee": round(float(oee), 4),
    }
