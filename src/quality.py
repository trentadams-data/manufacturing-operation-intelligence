"""Quality and defect analysis from ``quality_inspections``.

Defect rate is ``defect_count / sample_size`` aggregated by line, machine,
product family, and shift. Inspection defect rates are then extrapolated onto
realised production volume and valued at product unit margin to estimate the
financial impact of scrap and rework.
"""

from __future__ import annotations

import pandas as pd

from src.data_io import load_required, r, safe_div, write_json, write_table

# Share of defective units assumed unrecoverable (scrapped); the remainder is
# assumed reworked, which only forgoes part of the unit margin.
SCRAP_SHARE_OF_DEFECTS = 0.60
REWORK_MARGIN_LOSS_FRACTION = 0.30


def quality_summary(quality_inspections: pd.DataFrame) -> dict[str, float]:
    """Return a quality overview from inspection data (notebook compatibility)."""
    if quality_inspections.empty:
        return {"defect_rate": 0.0, "avg_measurement": 0.0, "sample_size": 0.0}

    defect_rate = safe_div(
        quality_inspections["defect_count"].sum(), quality_inspections["sample_size"].sum()
    )
    avg_measurement = quality_inspections["measurement_value"].mean()

    return {
        "defect_rate": r(defect_rate, 4),
        "avg_measurement": r(avg_measurement, 4),
        "sample_size": int(quality_inspections["sample_size"].sum()),
    }


def defect_rate_by(inspections: pd.DataFrame, key: str) -> pd.DataFrame:
    """Defect rate (defects / inspected units) grouped by a column."""
    grouped = (
        inspections.groupby(key)
        .agg(
            inspections=("inspection_id", "count"),
            sample_size=("sample_size", "sum"),
            defect_count=("defect_count", "sum"),
        )
        .reset_index()
    )
    grouped["defect_rate"] = grouped.apply(
        lambda row: r(safe_div(row["defect_count"], row["sample_size"]), 4), axis=1
    )
    return grouped.sort_values("defect_rate", ascending=False).reset_index(drop=True)


def run() -> dict[str, object]:
    """Compute defect breakdowns plus margin impact and write outputs."""
    inspections = load_required(
        "quality_inspections",
        [
            "inspection_id",
            "production_line",
            "machine_id",
            "product_id",
            "shift",
            "sample_size",
            "defect_count",
            "defect_type",
        ],
    )
    products = load_required(
        "products", ["product_id", "product_family", "unit_margin"]
    )
    production_runs = load_required(
        "production_runs", ["product_id", "actual_units"]
    )

    inspections = inspections.merge(
        products[["product_id", "product_family", "unit_margin"]],
        on="product_id",
        how="left",
    )

    overall_defect_rate = safe_div(
        inspections["defect_count"].sum(), inspections["sample_size"].sum()
    )

    by_line = defect_rate_by(inspections, "production_line")
    by_machine = defect_rate_by(inspections, "machine_id")
    by_family = defect_rate_by(inspections, "product_family")
    by_shift = defect_rate_by(inspections, "shift")

    defect_types = (
        inspections.groupby("defect_type")
        .agg(occurrences=("inspection_id", "count"), defect_count=("defect_count", "sum"))
        .reset_index()
        .sort_values("defect_count", ascending=False)
        .reset_index(drop=True)
    )
    total_defects = defect_types["defect_count"].sum()
    defect_types["share_pct"] = (
        defect_types["defect_count"].apply(lambda v: r(safe_div(v, total_defects) * 100.0, 2))
    )

    # Estimated financial impact: apply each product family's inspection defect
    # rate to that family's realised production volume, then value the defective
    # units (scrap at full margin, rework at a partial loss).
    family_defect_rate = (
        inspections.groupby("product_family")
        .apply(lambda g: safe_div(g["defect_count"].sum(), g["sample_size"].sum()),
               include_groups=False)
        .to_dict()
    )
    runs = production_runs.merge(
        products[["product_id", "product_family", "unit_margin"]],
        on="product_id",
        how="left",
    )
    runs["family_defect_rate"] = runs["product_family"].map(family_defect_rate).fillna(0.0)
    runs["estimated_defective_units"] = runs["actual_units"] * runs["family_defect_rate"]
    runs["scrap_impact"] = (
        runs["estimated_defective_units"] * SCRAP_SHARE_OF_DEFECTS * runs["unit_margin"]
    )
    runs["rework_impact"] = (
        runs["estimated_defective_units"]
        * (1.0 - SCRAP_SHARE_OF_DEFECTS)
        * runs["unit_margin"]
        * REWORK_MARGIN_LOSS_FRACTION
    )
    estimated_scrap_impact = float(runs["scrap_impact"].sum())
    estimated_rework_impact = float(runs["rework_impact"].sum())

    write_table(by_line, "defect_by_line.csv")
    write_table(by_machine, "defect_by_machine.csv")
    write_table(by_shift, "defect_by_shift.csv")
    write_table(defect_types, "defect_types.csv")

    summary = {
        "overall_defect_rate": r(overall_defect_rate, 4),
        "total_inspected_units": int(inspections["sample_size"].sum()),
        "total_defects": int(total_defects),
        "by_line": by_line.to_dict(orient="records"),
        "by_machine": by_machine.to_dict(orient="records"),
        "by_product_family": by_family.to_dict(orient="records"),
        "by_shift": by_shift.to_dict(orient="records"),
        "top_defect_types": defect_types.to_dict(orient="records"),
        "estimated_scrap_impact": r(estimated_scrap_impact),
        "estimated_rework_impact": r(estimated_rework_impact),
        "estimated_total_quality_impact": r(estimated_scrap_impact + estimated_rework_impact),
        "worst_line": by_line.iloc[0]["production_line"],
        "worst_machine": by_machine.iloc[0]["machine_id"],
        "top_defect_type": defect_types.iloc[0]["defect_type"],
    }
    write_json(summary, "defect_summary.json")

    print(
        f"Overall defect rate: {summary['overall_defect_rate']:.4f}. "
        f"Worst line: {summary['worst_line']}. "
        f"Est. quality impact: ${summary['estimated_total_quality_impact']:,.0f}"
    )
    return summary


def main() -> None:
    run()


if __name__ == "__main__":
    main()
