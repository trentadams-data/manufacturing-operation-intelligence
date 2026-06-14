"""Simple SPC helpers for quality analysis."""

from __future__ import annotations

import pandas as pd


def compute_spc_limits(quality_inspections: pd.DataFrame) -> dict[str, float]:
    """Compute simple mean and control limits for inspection measurements."""
    if quality_inspections.empty:
        return {"mean": 0.0, "upper_control": 0.0, "lower_control": 0.0}

    values = quality_inspections["measurement_value"]
    mean = values.mean()
    std = values.std(ddof=1)
    upper_control = mean + 3 * std
    lower_control = mean - 3 * std

    return {
        "mean": round(float(mean), 4),
        "upper_control": round(float(upper_control), 4),
        "lower_control": round(float(lower_control), 4),
    }
