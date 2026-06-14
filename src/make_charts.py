"""Generate clean, professional matplotlib charts for the portfolio.

Charts are intentionally simple (no heavy styling) and read from the tables and
JSON exports produced by the analytics modules. Saved as PNGs under
``outputs/charts``.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")  # headless, file-only rendering
import matplotlib.pyplot as plt
import pandas as pd

from src.config import WEB_EXPORT_DIR
from src.data_io import CHARTS_DIR, TABLES_DIR, ensure_output_dirs

plt.rcParams.update(
    {
        "figure.figsize": (9, 5),
        "figure.dpi": 120,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    }
)

PRIMARY = "#2b6cb0"
ACCENT = "#c05621"
NEUTRAL = "#4a5568"


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / name, bbox_inches="tight")
    plt.close(fig)


def chart_oee_trend() -> None:
    trend = pd.read_csv(TABLES_DIR / "oee_trend.csv", parse_dates=["week_start"])
    fig, ax = plt.subplots()
    ax.plot(trend["week_start"], trend["oee"], marker="o", color=PRIMARY, label="OEE")
    ax.plot(trend["week_start"], trend["availability"], color=NEUTRAL, alpha=0.7,
            linestyle="--", label="Availability")
    ax.plot(trend["week_start"], trend["quality"], color=ACCENT, alpha=0.7,
            linestyle=":", label="Quality")
    ax.set_title("Weekly OEE Trend")
    ax.set_xlabel("Week")
    ax.set_ylabel("Ratio")
    ax.set_ylim(0, 1)
    ax.legend(loc="lower left")
    fig.autofmt_xdate()
    _save(fig, "oee_trend.png")


def chart_downtime_pareto() -> None:
    pareto = pd.read_csv(TABLES_DIR / "downtime_by_reason.csv")
    fig, ax1 = plt.subplots()
    ax1.bar(pareto["downtime_reason"], pareto["downtime_minutes"], color=PRIMARY)
    ax1.set_ylabel("Downtime minutes")
    ax1.set_title("Downtime Pareto by Reason")
    ax1.tick_params(axis="x", rotation=45)
    for label in ax1.get_xticklabels():
        label.set_ha("right")

    ax2 = ax1.twinx()
    ax2.plot(pareto["downtime_reason"], pareto["cumulative_pct"], color=ACCENT,
             marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 105)
    ax2.grid(False)
    ax2.axhline(80, color=NEUTRAL, linestyle="--", alpha=0.6)
    _save(fig, "downtime_pareto.png")


def chart_defect_rate_by_line() -> None:
    defects = pd.read_csv(TABLES_DIR / "defect_by_line.csv").sort_values("defect_rate")
    fig, ax = plt.subplots()
    ax.barh(defects["production_line"], defects["defect_rate"] * 100, color=PRIMARY)
    ax.set_title("Defect Rate by Production Line")
    ax.set_xlabel("Defect rate (%)")
    ax.set_ylabel("Production line")
    _save(fig, "defect_rate_by_line.png")


def chart_spc_control_chart() -> None:
    data = json.loads((WEB_EXPORT_DIR / "spc_control_chart.json").read_text())
    points = pd.DataFrame(data["points"])
    fig, ax = plt.subplots()
    ax.plot(points["point"], points["measurement_value"], marker="o", color=PRIMARY,
            label="Measurement", zorder=3)

    out = points[points["out_of_control"]]
    if not out.empty:
        ax.scatter(out["point"], out["measurement_value"], color="#c53030", zorder=4,
                   label="Out of control")

    ax.axhline(data["centerline"], color=NEUTRAL, label="Centerline")
    ax.axhline(data["ucl"], color=ACCENT, linestyle="--", label="UCL / LCL")
    ax.axhline(data["lcl"], color=ACCENT, linestyle="--")
    ax.axhline(data["usl"], color="#c53030", linestyle=":", alpha=0.7,
               label="Spec limits")
    ax.axhline(data["lsl"], color="#c53030", linestyle=":", alpha=0.7)
    ax.set_title(f"Control Chart - {data['machine_id']} (Cpk {data['cpk']})")
    ax.set_xlabel("Inspection sequence")
    ax.set_ylabel("Measurement value")
    ax.legend(loc="best", fontsize=8)
    _save(fig, "spc_control_chart.png")


def chart_maintenance_risk() -> None:
    risk = pd.read_csv(TABLES_DIR / "high_risk_machines.csv")
    risk = risk.sort_values("avg_risk_probability").tail(8)
    colors = ["#c53030" if v >= 0.66 else "#dd6b20" if v >= 0.34 else PRIMARY
              for v in risk["avg_risk_probability"]]
    fig, ax = plt.subplots()
    ax.barh(risk["machine_id"], risk["avg_risk_probability"] * 100, color=colors)
    ax.set_title("Predicted 7-Day Failure Risk by Machine")
    ax.set_xlabel("Average failure probability (%)")
    ax.set_ylabel("Machine")
    ax.set_xlim(0, 100)
    _save(fig, "maintenance_risk_top_machines.png")


def run() -> list[str]:
    """Generate every chart and return the filenames written."""
    ensure_output_dirs()
    charts = [
        ("oee_trend.png", chart_oee_trend),
        ("downtime_pareto.png", chart_downtime_pareto),
        ("defect_rate_by_line.png", chart_defect_rate_by_line),
        ("spc_control_chart.png", chart_spc_control_chart),
        ("maintenance_risk_top_machines.png", chart_maintenance_risk),
    ]
    written = []
    for name, builder in charts:
        builder()
        written.append(name)
        print(f"  chart: {name}")
    return written


def main() -> None:
    run()


if __name__ == "__main__":
    main()
