"""Quality analysis helpers."""

from __future__ import annotations

import pandas as pd


def quality_summary(quality_inspections: pd.DataFrame) -> dict[str, float]:
    """Return a quality overview from inspection data."""
    if quality_inspections.empty:
        return {"defect_rate": 0.0, "avg_measurement": 0.0, "sample_size": 0.0}

    defect_rate = quality_inspections["defect_count"].sum() / max(quality_inspections["sample_size"].sum(), 1.0)
    avg_measurement = quality_inspections["measurement_value"].mean()

    return {
        "defect_rate": round(float(defect_rate), 4),
        "avg_measurement": round(float(avg_measurement), 4),
        "sample_size": int(quality_inspections["sample_size"].sum()),
    }
