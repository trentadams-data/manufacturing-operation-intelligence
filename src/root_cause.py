"""Root-cause summary helpers."""

from __future__ import annotations

import pandas as pd


def summarize_root_causes(machine_events: pd.DataFrame, maintenance_logs: pd.DataFrame, quality_inspections: pd.DataFrame) -> dict[str, list[str]]:
    """Create a simple readout of candidate root-cause themes."""
    downtime_reasons = machine_events["downtime_reason"].astype(str).value_counts().head(3).index.tolist()
    maintenance_issues = maintenance_logs["issue_found"].astype(str).value_counts().head(3).index.tolist()
    defect_types = quality_inspections["defect_type"].astype(str).value_counts().head(3).index.tolist()

    return {
        "top_downtime_reasons": downtime_reasons,
        "top_maintenance_issues": maintenance_issues,
        "top_defect_types": defect_types,
    }
