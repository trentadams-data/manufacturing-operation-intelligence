"""Statistical Process Control (SPC) analysis from ``quality_inspections``.

Each machine measures a single characteristic against a constant target and
spec window, so a process stream is defined per ``machine_id``. For each stream
we build an individuals (I) control chart and compute capability indices.

Control limits use the average moving range (MR-bar) estimate of sigma, the
standard approach for individuals charts:

    sigma_hat = MR_bar / 1.128      (1.128 = d2 for n = 2)
    centerline = process mean
    UCL / LCL  = mean +/- 3 * sigma_hat

Capability uses the same within-process sigma estimate:

    Cp  = (USL - LSL) / (6 * sigma_hat)
    Cpk = min(USL - mean, mean - LSL) / (3 * sigma_hat)
"""

from __future__ import annotations

import pandas as pd

from src.data_io import load_required, r, safe_div, write_json, write_table

# d2 control-chart constant for a moving range of two consecutive observations.
D2_N2 = 1.128


def compute_spc_limits(quality_inspections: pd.DataFrame) -> dict[str, float]:
    """Compute simple mean and 3-sigma control limits (notebook compatibility)."""
    if quality_inspections.empty:
        return {"mean": 0.0, "upper_control": 0.0, "lower_control": 0.0}

    values = quality_inspections["measurement_value"]
    mean = values.mean()
    std = values.std(ddof=1)
    return {
        "mean": r(mean, 4),
        "upper_control": r(mean + 3 * std, 4),
        "lower_control": r(mean - 3 * std, 4),
    }


def _process_stats(group: pd.DataFrame) -> dict[str, float]:
    """SPC statistics and capability indices for one ordered process stream."""
    ordered = group.sort_values("date")
    values = ordered["measurement_value"].to_numpy(dtype=float)
    mean = float(values.mean())

    moving_range = abs(pd.Series(values).diff()).dropna()
    mr_bar = float(moving_range.mean()) if not moving_range.empty else 0.0
    sigma_hat = safe_div(mr_bar, D2_N2)
    # Fall back to the overall standard deviation if the moving range collapses.
    if sigma_hat <= 1e-9 and len(values) > 1:
        sigma_hat = float(pd.Series(values).std(ddof=1))

    ucl = mean + 3 * sigma_hat
    lcl = mean - 3 * sigma_hat

    usl = float(ordered["upper_spec_limit"].iloc[0])
    lsl = float(ordered["lower_spec_limit"].iloc[0])
    target = float(ordered["target_value"].iloc[0])

    out_of_control = int(((values > ucl) | (values < lcl)).sum())
    out_of_spec = int(((values > usl) | (values < lsl)).sum())

    cp = safe_div(usl - lsl, 6 * sigma_hat) if sigma_hat > 1e-9 else None
    cpk = (
        safe_div(min(usl - mean, mean - lsl), 3 * sigma_hat)
        if sigma_hat > 1e-9
        else None
    )

    return {
        "points": int(len(values)),
        "mean": r(mean, 4),
        "std_dev": r(sigma_hat, 4),
        "centerline": r(mean, 4),
        "ucl": r(ucl, 4),
        "lcl": r(lcl, 4),
        "target": r(target, 4),
        "lsl": r(lsl, 4),
        "usl": r(usl, 4),
        "points_out_of_control": out_of_control,
        "points_out_of_spec": out_of_spec,
        "cp": r(cp, 3) if cp is not None else None,
        "cpk": r(cpk, 3) if cpk is not None else None,
    }


def control_chart_data(group: pd.DataFrame, stats: dict[str, float]) -> pd.DataFrame:
    """Build a per-point, chart-ready dataset for one process stream."""
    ordered = group.sort_values("date").reset_index(drop=True)
    chart = pd.DataFrame(
        {
            "point": range(1, len(ordered) + 1),
            "date": ordered["date"].dt.strftime("%Y-%m-%d"),
            "machine_id": ordered["machine_id"],
            "measurement_value": ordered["measurement_value"].round(4),
        }
    )
    chart["centerline"] = stats["centerline"]
    chart["ucl"] = stats["ucl"]
    chart["lcl"] = stats["lcl"]
    chart["usl"] = stats["usl"]
    chart["lsl"] = stats["lsl"]
    chart["out_of_control"] = (
        (chart["measurement_value"] > stats["ucl"])
        | (chart["measurement_value"] < stats["lcl"])
    )
    chart["out_of_spec"] = (
        (chart["measurement_value"] > stats["usl"])
        | (chart["measurement_value"] < stats["lsl"])
    )
    return chart


def run() -> dict[str, object]:
    """Compute SPC summaries for every process and export a sample control chart."""
    inspections = load_required(
        "quality_inspections",
        [
            "machine_id",
            "date",
            "measurement_value",
            "target_value",
            "lower_spec_limit",
            "upper_spec_limit",
        ],
    )

    summary_rows = []
    stats_by_machine = {}
    for machine_id, group in inspections.groupby("machine_id"):
        if len(group) < 2:
            continue
        stats = _process_stats(group)
        stats_by_machine[machine_id] = (group, stats)
        row = {"machine_id": machine_id}
        row.update(stats)
        summary_rows.append(row)

    spc_summary = pd.DataFrame(summary_rows).sort_values("cpk").reset_index(drop=True)

    # Choose the lowest-capability process with enough points as the showcase
    # control chart for the website (it tells the most interesting story).
    eligible = {k: v for k, v in stats_by_machine.items() if v[1]["points"] >= 10}
    chart_pool = eligible or stats_by_machine
    chart_machine = min(chart_pool, key=lambda k: chart_pool[k][1]["cpk"] or 0.0)
    chart_group, chart_stats = chart_pool[chart_machine]
    chart = control_chart_data(chart_group, chart_stats)

    write_table(spc_summary, "spc_summary.csv")
    write_table(chart, "spc_control_chart_data.csv")

    findings = {
        "process_count": int(len(spc_summary)),
        "avg_cpk": r(spc_summary["cpk"].dropna().mean(), 3),
        "min_cpk": r(spc_summary["cpk"].dropna().min(), 3),
        "processes_below_cpk_1_33": int((spc_summary["cpk"] < 1.33).sum()),
        "processes_below_cpk_1_0": int((spc_summary["cpk"] < 1.0).sum()),
        "total_points_out_of_control": int(spc_summary["points_out_of_control"].sum()),
        "total_points_out_of_spec": int(spc_summary["points_out_of_spec"].sum()),
        "lowest_capability_machine": chart_machine,
        "by_machine": spc_summary.to_dict(orient="records"),
    }
    write_json(findings, "spc_findings.json")

    chart_export = {
        "machine_id": chart_machine,
        "centerline": chart_stats["centerline"],
        "ucl": chart_stats["ucl"],
        "lcl": chart_stats["lcl"],
        "usl": chart_stats["usl"],
        "lsl": chart_stats["lsl"],
        "cp": chart_stats["cp"],
        "cpk": chart_stats["cpk"],
        "points": chart.to_dict(orient="records"),
    }
    write_json(chart_export, "spc_control_chart.json")

    print(
        f"SPC: {findings['process_count']} processes, avg Cpk {findings['avg_cpk']}. "
        f"Showcase chart: {chart_machine} (Cpk {chart_stats['cpk']})"
    )
    return findings


def main() -> None:
    run()


if __name__ == "__main__":
    main()
