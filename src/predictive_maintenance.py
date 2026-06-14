"""Simple predictive maintenance indicators."""

from __future__ import annotations

import pandas as pd


def create_risk_signal(sensor_readings: pd.DataFrame) -> pd.DataFrame:
    """Create a simple risk score from temperature, vibration, and alarm counts."""
    if sensor_readings.empty:
        return sensor_readings.copy()

    sensor_readings = sensor_readings.copy()
    sensor_readings["risk_score"] = (
        0.35 * (sensor_readings["temperature_c"] / 80.0)
        + 0.40 * (sensor_readings["vibration_mm_s"] / 4.0)
        + 0.25 * (sensor_readings["alarm_count"] / 3.0)
    )
    return sensor_readings
