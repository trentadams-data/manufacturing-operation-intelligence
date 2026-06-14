"""Downtime analysis from ``machine_events``.

Breaks total downtime into planned vs unplanned, attributes it by reason,
machine, line, and shift, and builds a Pareto view (sorted contribution plus
cumulative share) to highlight the vital few causes that drive most loss.
"""

from __future__ import annotations

import pandas as pd

from src.data_io import load_required, r, safe_div, write_json, write_table


def downtime_summary(machine_events: pd.DataFrame) -> pd.DataFrame:
    """Return downtime totals by reason and severity (notebook compatibility)."""
    if machine_events.empty:
        return pd.DataFrame(columns=["downtime_reason", "severity", "downtime_minutes"])

    return (
        machine_events.groupby(["downtime_reason", "severity"], as_index=False)["downtime_minutes"]
        .sum()
        .sort_values("downtime_minutes", ascending=False)
    )


def _group_downtime(events: pd.DataFrame, key: str) -> pd.DataFrame:
    """Aggregate downtime minutes and event counts by a grouping column."""
    grouped = (
        events.groupby(key)
        .agg(downtime_minutes=("downtime_minutes", "sum"), events=("event_id", "count"))
        .reset_index()
        .sort_values("downtime_minutes", ascending=False)
        .reset_index(drop=True)
    )
    grouped["downtime_minutes"] = grouped["downtime_minutes"].round(1)
    grouped["avg_minutes_per_event"] = (
        grouped["downtime_minutes"] / grouped["events"].clip(lower=1)
    ).round(1)
    return grouped


def pareto_by_reason(events: pd.DataFrame) -> pd.DataFrame:
    """Pareto table of downtime by reason with cumulative share of total minutes."""
    grouped = _group_downtime(events, "downtime_reason")
    total = grouped["downtime_minutes"].sum()
    grouped["share_pct"] = (
        grouped["downtime_minutes"].apply(lambda v: safe_div(v, total) * 100.0).round(2)
    )
    grouped["cumulative_pct"] = grouped["share_pct"].cumsum().round(2)
    return grouped


def run() -> dict[str, object]:
    """Compute downtime breakdowns and write tables and JSON exports."""
    events = load_required(
        "machine_events",
        [
            "event_id",
            "event_type",
            "downtime_reason",
            "downtime_minutes",
            "machine_id",
            "production_line",
            "shift",
        ],
    )

    total_downtime = float(events["downtime_minutes"].sum())
    by_type = (
        events.groupby("event_type")["downtime_minutes"].sum().round(1).to_dict()
    )
    planned_minutes = float(by_type.get("planned", 0.0))
    unplanned_minutes = float(by_type.get("unplanned", 0.0))

    by_reason = pareto_by_reason(events)
    by_machine = _group_downtime(events, "machine_id")
    by_line = _group_downtime(events, "production_line")
    by_shift = _group_downtime(events, "shift")

    # Top recurring issues: rank reasons by how often they occur, not just minutes,
    # since frequent short stops are strong candidates for standard-work fixes.
    recurring = (
        events.groupby("downtime_reason")
        .agg(events=("event_id", "count"), downtime_minutes=("downtime_minutes", "sum"))
        .reset_index()
        .sort_values("events", ascending=False)
        .head(5)
    )
    recurring["downtime_minutes"] = recurring["downtime_minutes"].round(1)

    write_table(by_reason, "downtime_by_reason.csv")
    write_table(by_machine, "downtime_by_machine.csv")
    write_table(by_line, "downtime_by_line.csv")

    summary = {
        "total_downtime_minutes": r(total_downtime, 1),
        "total_downtime_hours": r(total_downtime / 60.0, 1),
        "planned_minutes": r(planned_minutes, 1),
        "unplanned_minutes": r(unplanned_minutes, 1),
        "unplanned_share_pct": r(safe_div(unplanned_minutes, total_downtime) * 100.0, 2),
        "events": int(len(events)),
        "by_reason": by_reason.to_dict(orient="records"),
        "by_machine": by_machine.to_dict(orient="records"),
        "by_line": by_line.to_dict(orient="records"),
        "by_shift": by_shift.to_dict(orient="records"),
        "top_recurring_issues": recurring.to_dict(orient="records"),
        "worst_reason": by_reason.iloc[0]["downtime_reason"],
        "worst_machine": by_machine.iloc[0]["machine_id"],
    }
    write_json(summary, "downtime_summary.json")
    write_json(by_reason.to_dict(orient="records"), "downtime_pareto.json")

    print(
        f"Total downtime: {total_downtime/60.0:.1f} h "
        f"(unplanned {summary['unplanned_share_pct']}%). "
        f"Top reason: {summary['worst_reason']}"
    )
    return summary


def main() -> None:
    run()


if __name__ == "__main__":
    main()
