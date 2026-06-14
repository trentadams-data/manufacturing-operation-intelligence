"""Root-cause synthesis.

Reads the JSON findings produced by the OEE, downtime, quality, SPC, and
predictive-maintenance modules and translates them into a single, business-
readable table of findings, likely drivers, impact, recommended actions, and
priority. This is the layer that turns analytics output into decisions.
"""

from __future__ import annotations

import json

import pandas as pd

from src.config import WEB_EXPORT_DIR
from src.data_io import write_json, write_table

COLUMNS = [
    "finding",
    "likely_driver",
    "business_impact",
    "recommended_action",
    "priority",
    "affected_area",
]


def _load(name: str) -> dict:
    """Load a previously exported web JSON document by filename."""
    path = WEB_EXPORT_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing '{path}'. Run the upstream analytics modules before root_cause."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_root_causes(
    machine_events: pd.DataFrame,
    maintenance_logs: pd.DataFrame,
    quality_inspections: pd.DataFrame,
) -> dict[str, list[str]]:
    """Lightweight theme readout retained for notebook compatibility."""
    return {
        "top_downtime_reasons": machine_events["downtime_reason"]
        .astype(str)
        .value_counts()
        .head(3)
        .index.tolist(),
        "top_maintenance_issues": maintenance_logs["issue_found"]
        .astype(str)
        .value_counts()
        .head(3)
        .index.tolist(),
        "top_defect_types": quality_inspections["defect_type"]
        .astype(str)
        .value_counts()
        .head(3)
        .index.tolist(),
    }


def build_findings() -> pd.DataFrame:
    """Assemble the cross-domain root-cause table from exported findings."""
    oee = _load("oee_summary.json")
    downtime = _load("downtime_summary.json")
    quality = _load("defect_summary.json")
    spc = _load("spc_findings.json")
    pm = _load("predictive_maintenance_results.json")

    findings: list[dict[str, str]] = []

    # --- OEE -------------------------------------------------------------
    worst_machine = next(
        (m for m in oee["by_machine"] if m["machine_id"] == oee["worst_machine"]),
        oee["by_machine"][-1],
    )
    findings.append(
        {
            "finding": (
                f"{worst_machine['machine_id']} has the lowest OEE in the plant "
                f"({worst_machine['oee']:.1%})"
            ),
            "likely_driver": (
                "Availability loss from unplanned stops and below-target performance"
            ),
            "business_impact": "Reduced effective capacity and higher unit cost on this asset",
            "recommended_action": (
                "Prioritise this machine for a focused OEE improvement review "
                "(setup reduction, minor-stop elimination)"
            ),
            "priority": "High",
            "affected_area": f"Line {worst_machine['production_line'] if 'production_line' in worst_machine else ''} / {worst_machine['machine_id']}".strip(" /"),
        }
    )

    # --- Downtime --------------------------------------------------------
    findings.append(
        {
            "finding": (
                f"Unplanned downtime accounts for {downtime['unplanned_share_pct']:.0f}% "
                f"of all downtime; '{downtime['worst_reason']}' is the largest reason"
            ),
            "likely_driver": f"Recurring '{downtime['worst_reason']}' events, concentrated on {downtime['worst_machine']}",
            "business_impact": (
                f"~{downtime['unplanned_minutes']/60:.0f} operating hours lost to unplanned stops"
            ),
            "recommended_action": (
                "Launch a Pareto-led downtime reduction effort on the top reason "
                "and condition-monitor the worst machine"
            ),
            "priority": "High",
            "affected_area": f"{downtime['worst_machine']}",
        }
    )

    # --- Quality ---------------------------------------------------------
    findings.append(
        {
            "finding": (
                f"{quality['worst_line']} has the highest defect rate; "
                f"'{quality['top_defect_type']}' is the most common defect"
            ),
            "likely_driver": "Process variation and shift-related quality differences",
            "business_impact": (
                f"~${quality['estimated_total_quality_impact']:,.0f} estimated scrap and rework margin loss"
            ),
            "recommended_action": (
                "Stand up a containment and corrective-action plan for the top defect "
                "type on the worst line"
            ),
            "priority": "High",
            "affected_area": f"{quality['worst_line']}",
        }
    )

    # --- SPC -------------------------------------------------------------
    spc_priority = "High" if spc["processes_below_cpk_1_33"] > 0 else "Medium"
    findings.append(
        {
            "finding": (
                f"{spc['processes_below_cpk_1_33']} process(es) below Cpk 1.33; "
                f"{spc['lowest_capability_machine']} is the least capable"
            ),
            "likely_driver": "Excess common-cause variation relative to the spec window",
            "business_impact": (
                f"{spc['total_points_out_of_spec']} inspection point(s) outside specification "
                "raise escape and rework risk"
            ),
            "recommended_action": (
                "Centre and tighten the lowest-capability process; investigate any "
                "out-of-control points for special causes"
            ),
            "priority": spc_priority,
            "affected_area": f"{spc['lowest_capability_machine']}",
        }
    )

    # --- Predictive maintenance -----------------------------------------
    top_risk = pm["high_risk_machines"][0]
    findings.append(
        {
            "finding": (
                f"{top_risk['machine_id']} carries the highest predicted failure risk "
                f"({top_risk['avg_risk_probability']:.0%}) over the next 7 days"
            ),
            "likely_driver": (
                "Elevated vibration/temperature trend, machine age, and recent event history"
            ),
            "business_impact": "High likelihood of an unplanned stop and reactive repair cost",
            "recommended_action": (
                f"Schedule a proactive inspection on {top_risk['machine_id']} and review "
                f"the {pm['recommended_model']} watchlist weekly (recall {pm['recommended_model_recall']:.2f})"
            ),
            "priority": "High",
            "affected_area": f"{top_risk['machine_id']}",
        }
    )

    return pd.DataFrame(findings, columns=COLUMNS)


def run() -> dict[str, object]:
    """Build the root-cause table and write the table and JSON exports."""
    findings = build_findings()
    write_table(findings, "root_cause_summary.csv")

    payload = {
        "finding_count": int(len(findings)),
        "high_priority_count": int((findings["priority"] == "High").sum()),
        "findings": findings.to_dict(orient="records"),
    }
    write_json(payload, "root_cause_summary.json")

    print(f"Root-cause summary: {len(findings)} findings "
          f"({payload['high_priority_count']} high priority)")
    return payload


def main() -> None:
    run()


if __name__ == "__main__":
    main()
