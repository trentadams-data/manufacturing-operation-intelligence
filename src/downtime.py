"""Downtime analysis helpers."""

from __future__ import annotations

import pandas as pd


def downtime_summary(machine_events: pd.DataFrame) -> pd.DataFrame:
    """Return downtime totals by reason and severity."""
    if machine_events.empty:
        return pd.DataFrame(columns=["downtime_reason", "severity", "downtime_minutes"])

    return (
        machine_events.groupby(["downtime_reason", "severity"], as_index=False)["downtime_minutes"]
        .sum()
        .sort_values("downtime_minutes", ascending=False)
    )
