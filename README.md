# Manufacturing Operations Intelligence

OEE, downtime, quality, SPC, and predictive-maintenance analytics for a simulated
manufacturing plant — an end-to-end Python case study that turns raw production,
maintenance, quality, and sensor data into decision-ready operational insight and
a web-ready portfolio export.

> **Dataset is synthetic and created for portfolio demonstration purposes.**

---

## Project overview

This project recreates the data environment of a small multi-plant manufacturer
and runs a complete analytics pipeline on it: it generates realistic synthetic
data, computes the metrics plant leaders act on, trains a predictive-maintenance
model, connects the findings into root-cause recommendations, and exports a
single JSON document plus charts for a React/Vite portfolio website.

The entire project runs from one command and is fully reproducible (fixed random
seed), with an input-validation layer and a standalone output validator.

**Headline results:** 85.3% plant OEE · 96.4% first pass yield · 66% of downtime
unplanned · Random Forest maintenance model with ~0.86 recall and ~0.93 ROC AUC.

## Business problem

Manufacturing leaders rarely lack data — they lack a connected view of it.
Production, maintenance, quality, and sensor systems each tell part of the story,
but the questions that drive margin sit across all of them. This project answers
them in one reproducible pipeline.

## Analytics questions

1. Which lines and machines are underperforming on OEE, and by how much?
2. Where is downtime concentrated, and how much of it is unplanned (avoidable)?
3. Which machines are most likely to fail within the next seven days?
4. Which products, lines, and shifts drive the most defects and scrap?
5. How capable are the processes (Cp, Cpk), and where is the risk of escapes?
6. What is the cost of poor quality and lost availability in margin terms?

## Dataset description

Synthetic data is generated across seven related tables:

| Table | Description |
| --- | --- |
| `production_runs` | Per-run planned/operating time, planned/actual/good/scrap/rework units |
| `machine_events` | Planned and unplanned downtime events with reason and severity |
| `maintenance_logs` | Preventive, corrective, inspection, and replacement maintenance |
| `quality_inspections` | Sample sizes, defect counts/types, and SPC measurements vs. spec |
| `sensor_readings` | Temperature, vibration, pressure, runtime hours, and alarm counts |
| `products` | Product family, standard cycle time, and unit margin |
| `work_centers` | Machine plant/line, type, install year, and criticality |

The data is engineered to reflect real plant behaviour: older machines fail more
often, vibration and temperature rise ahead of failures, certain shifts carry
higher defect rates, and specific machines show recurring downtime patterns.
Scale: ~1,450 production runs, ~260 machine events, ~180 quality inspections, and
~1,250 sensor readings across eight machines and six product families.

## Methodology

Full detail is in [docs/methodology.md](docs/methodology.md). In brief:

- **KPIs** — scrap/rework rates, first pass yield, throughput, schedule
  attainment, production variance, and margin-based scrap and downtime cost.
- **OEE** — Availability × Performance × Quality, aggregated on summed
  numerators/denominators at plant, line, machine, shift, and weekly-trend levels,
  with divide-by-zero guards and `[0, 1]` clipping.
- **Downtime** — planned vs. unplanned split, breakdowns by reason/machine/line/
  shift, Pareto analysis, and recurring-issue ranking.
- **Quality** — defect rates by line/machine/family/shift, top defect types, and
  estimated scrap/rework margin impact.
- **SPC** — individuals control charts (moving-range sigma) and capability
  indices (Cp, Cpk) per machine, with out-of-control and out-of-spec counts.
- **Predictive maintenance** — a `failure_within_7_days` target engineered from
  events and corrective maintenance, with sensor-trend, age, and history
  features; Logistic Regression and Random Forest models evaluated with a
  recall-first lens.
- **Root cause** — cross-domain findings synthesised into a business-readable
  table of drivers, impacts, actions, and priorities.

## Key findings

Full write-up in [docs/executive_summary.md](docs/executive_summary.md).

- **Plant OEE is 85.3%** (Availability 90.1%, Performance 98.2%, Quality 96.4%);
  availability loss from unplanned stops is the primary constraint.
- **66% of downtime is unplanned**, led by power fluctuation, overheating, and
  bearing faults.
- **M-202 (Line B)** is the lowest-OEE asset, the highest-downtime machine, and a
  top maintenance-risk machine — losses on three fronts from one asset.
- **Random Forest** predicts near-term failures at ~0.86 recall / ~0.93 ROC AUC,
  far ahead of Logistic Regression (~0.64 recall).
- **Seven of eight processes** sit below the Cpk 1.33 capability target;
  **M-102** is the least capable.
- Estimated cost of poor quality is **~$264K** in margin, with a further **~$80K**
  lost to unplanned downtime.

## Project structure

```text
manufacturing-operations-intelligence/
├── README.md
├── Makefile
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/
│   ├── processed/        # synthetic input CSVs (committed)
│   └── web_exports/      # web-ready JSON (generated)
├── notebooks/            # narrative walkthrough notebooks
├── src/
│   ├── config.py             # paths, machine/product specs, seed
│   ├── data_io.py            # shared loaders, validators, writers
│   ├── generate_data.py      # synthetic data generator
│   ├── calculate_kpis.py     # production KPIs
│   ├── oee.py                # OEE at every level
│   ├── downtime.py           # downtime + Pareto
│   ├── quality.py            # defect analysis
│   ├── spc.py                # SPC + capability
│   ├── predictive_maintenance.py  # failure-risk models
│   ├── root_cause.py         # cross-domain recommendations
│   ├── make_charts.py        # matplotlib charts
│   ├── export_for_web.py     # combined case-study JSON
│   ├── run_pipeline.py       # one-command pipeline runner
│   └── validate_outputs.py   # output completeness/validity checks
├── outputs/
│   ├── charts/           # generated PNG charts
│   ├── tables/           # generated CSV tables
│   └── models/
└── docs/
    ├── methodology.md
    ├── data_dictionary.md
    ├── executive_summary.md
    ├── website_case_study_copy.md
    └── frontend_integration.md
```

## How to run

Requires Python 3.11+.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full pipeline (generate data -> analytics -> exports -> charts)
python src/run_pipeline.py

# 3. Validate that all expected outputs exist and are well-formed
python src/validate_outputs.py
```

Or use the Makefile shortcuts:

```bash
make setup      # install dependencies
make run        # run the full pipeline
make validate   # validate outputs
make clean      # remove generated tables, charts, and web exports
```

Individual stages can also be run on their own, for example
`python -m src.oee` or `python -m src.predictive_maintenance`. The data
generator is also available directly via `python src/generate_data.py`.

## Generated outputs

Running the pipeline produces:

- **`outputs/tables/`** — 18 analysis tables in CSV form (KPIs, OEE, downtime,
  quality, SPC, predictive maintenance, root cause).
- **`outputs/charts/`** — `oee_trend.png`, `downtime_pareto.png`,
  `defect_rate_by_line.png`, `spc_control_chart.png`,
  `maintenance_risk_top_machines.png`.
- **`data/web_exports/`** — per-domain JSON plus the combined
  `manufacturing_case_study.json`, structured for direct frontend use with these
  top-level keys: `project`, `executive_kpis`, `dataset_profile`, `oee`,
  `downtime`, `quality`, `spc`, `predictive_maintenance`, `root_cause`,
  `executive_recommendations`, and `charts`.

## Website integration

The project is designed to feed a Bolt.new / React / Vite portfolio site. See
[docs/frontend_integration.md](docs/frontend_integration.md) for copy paths,
a React fetch example, and TypeScript interfaces. Polished page copy is in
[docs/website_case_study_copy.md](docs/website_case_study_copy.md).

In short, copy `data/web_exports/*.json` into the site's
`public/data/manufacturing/` and `outputs/charts/*.png` into
`public/images/manufacturing/`; the chart `image` paths in the JSON already match
that location.

## Limitations

- The dataset is synthetic. Patterns are intentionally realistic but simplified,
  so absolute figures are illustrative, not benchmarks.
- The predictive-maintenance panel covers the sensor-data window, which is shorter
  than the full production window; the positive rate is therefore higher than a
  real fleet would typically show.
- Cost estimates use unit margin as a proxy for the value of a unit and apply
  simple scrap/rework assumptions documented in the code.
- SPC assumes one measured characteristic per machine with stable spec limits.

## Future enhancements

- Add time-series cross-validation and probability calibration to the maintenance
  model, and persist the trained model artifact.
- Extend SPC with additional Western Electric run rules and per-product charts.
- Add a small API or scheduled job to refresh exports automatically.
- Introduce cost parameters as configurable inputs rather than fixed assumptions.

## Notes

- All data in this repository is synthetic and intended for educational and
  portfolio purposes.
- No API keys, cloud services, or external data dependencies are required.
