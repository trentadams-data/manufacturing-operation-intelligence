"""Overall Equipment Effectiveness (OEE) at multiple aggregation levels.

OEE = Availability x Performance x Quality, computed from ``production_runs``:

* Availability = operating_minutes / planned_minutes
* Performance  = ideal_runtime_for_actual_output / operating_time
                 where ideal runtime = actual_units * ideal_cycle_time_seconds
* Quality      = good_units / actual_units

Assumptions and safeguards:

* Every ratio is computed on summed numerators/denominators within a group so
  that larger runs are weighted by their true time/volume contribution.
* All ratios are guarded against divide-by-zero via :func:`safe_div`.
* Availability and Quality are clipped to [0, 1]. Performance is also clipped to
  [0, 1]: synthetic runs occasionally beat the ideal cycle time, which would push
  Performance above 100%. Capping at 1.0 keeps OEE interpretable as a loss model
  (you cannot be "better than perfect"); the small amount of clipping is noted in
  the trend so the assumption is transparent.
"""

from __future__ import annotations

import pandas as pd

from src.data_io import load_required, r, safe_div, write_json, write_table


def _oee_components(group: pd.DataFrame) -> dict[str, float]:
    """Compute clipped OEE components for a set of production runs."""
    planned_minutes = float(group["planned_minutes"].sum())
    operating_minutes = float(group["operating_minutes"].sum())
    actual_units = float(group["actual_units"].sum())
    good_units = float(group["good_units"].sum())
    ideal_runtime_seconds = float(
        (group["actual_units"] * group["ideal_cycle_time_seconds"]).sum()
    )
    operating_seconds = operating_minutes * 60.0

    availability = min(1.0, max(0.0, safe_div(operating_minutes, planned_minutes)))
    performance = min(1.0, max(0.0, safe_div(ideal_runtime_seconds, operating_seconds)))
    quality = min(1.0, max(0.0, safe_div(good_units, actual_units)))
    oee = availability * performance * quality

    return {
        "runs": int(len(group)),
        "availability": r(availability, 4),
        "performance": r(performance, 4),
        "quality": r(quality, 4),
        "oee": r(oee, 4),
    }


def calculate_oee(production_runs: pd.DataFrame) -> dict[str, float]:
    """Return plant-wide OEE components (kept for notebook compatibility)."""
    if production_runs.empty:
        return {"availability": 0.0, "performance": 0.0, "quality": 0.0, "oee": 0.0}
    components = _oee_components(production_runs)
    return {
        "availability": components["availability"],
        "performance": components["performance"],
        "quality": components["quality"],
        "oee": components["oee"],
    }


def oee_by(production_runs: pd.DataFrame, key: str) -> pd.DataFrame:
    """OEE components grouped by a single column (line, machine, shift, ...)."""
    rows = []
    for value, group in production_runs.groupby(key):
        record = {key: value}
        record.update(_oee_components(group))
        rows.append(record)
    frame = pd.DataFrame(rows).sort_values("oee", ascending=False).reset_index(drop=True)
    return frame


def oee_trend(production_runs: pd.DataFrame) -> pd.DataFrame:
    """Weekly plant-wide OEE trend (weeks smooth the daily noise for charts)."""
    runs = production_runs.copy()
    runs["week_start"] = runs["date"].dt.to_period("W-SUN").dt.start_time
    rows = []
    for week, group in runs.groupby("week_start"):
        record = {"week_start": week.strftime("%Y-%m-%d")}
        record.update(_oee_components(group))
        rows.append(record)
    return pd.DataFrame(rows).sort_values("week_start").reset_index(drop=True)


def run() -> dict[str, object]:
    """Compute OEE at every level and write tables and JSON exports."""
    production_runs = load_required(
        "production_runs",
        [
            "planned_minutes",
            "operating_minutes",
            "actual_units",
            "good_units",
            "ideal_cycle_time_seconds",
            "production_line",
            "machine_id",
            "shift",
            "date",
        ],
    )

    plant = _oee_components(production_runs)
    by_line = oee_by(production_runs, "production_line")
    by_machine = oee_by(production_runs, "machine_id")
    by_shift = oee_by(production_runs, "shift")
    trend = oee_trend(production_runs)

    write_table(by_line, "oee_by_line.csv")
    write_table(by_machine, "oee_by_machine.csv")
    write_table(by_shift, "oee_by_shift.csv")
    write_table(trend, "oee_trend.csv")

    summary = {
        "plant_total": plant,
        "by_line": by_line.to_dict(orient="records"),
        "by_machine": by_machine.to_dict(orient="records"),
        "by_shift": by_shift.to_dict(orient="records"),
        "worst_line": by_line.iloc[-1]["production_line"],
        "best_line": by_line.iloc[0]["production_line"],
        "worst_machine": by_machine.iloc[-1]["machine_id"],
    }
    write_json(summary, "oee_summary.json")
    write_json(trend.to_dict(orient="records"), "oee_trend.json")

    print(
        "Plant OEE: "
        f"A={plant['availability']} P={plant['performance']} "
        f"Q={plant['quality']} OEE={plant['oee']}"
    )
    return summary


def main() -> None:
    run()


if __name__ == "__main__":
    main()
