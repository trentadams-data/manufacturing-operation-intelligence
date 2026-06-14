# Manufacturing Operations Intelligence

A Python-based analytics and business intelligence case study for a manufacturing operations portfolio project. The goal is to simulate realistic plant data, measure production performance, and present operational insights through dashboards, charts, and export-ready materials.

## Business problem

Manufacturing leaders need fast answers to questions such as:

- Which lines are underperforming?
- Where do downtime losses occur most often?
- Which machines are at highest risk of failure?
- Which products and shifts drive the most defects?
- What signals can be used to prioritize maintenance actions?

This project recreates a synthetic environment for those questions so the analysis can be explained clearly in a portfolio setting.

## Dataset overview

The project generates synthetic manufacturing data across seven tables:

- production_runs
- machine_events
- maintenance_logs
- quality_inspections
- sensor_readings
- products
- work_centers

The data is designed to reflect realistic patterns: older machines have higher failure risk, vibration and temperature increase failure likelihood, some shifts have slightly different defect rates, repeated downtime issues appear on specific machines, and quality data supports SPC-style analysis.

## Analytical objectives

1. Calculate production KPIs such as throughput, yield, OEE, scrap rate, and utilization.
2. Analyze downtime by reason, severity, shift, and machine.
3. Build predictive maintenance signals from sensor and maintenance history.
4. Explore quality performance and SPC indicators.
5. Produce export-ready summaries for a web portfolio.

## Project structure

```text
manufacturing-operations-intelligence/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/
│   ├── processed/
│   └── web_exports/
├── notebooks/
│   ├── 01_data_generation.ipynb
│   ├── 02_kpi_oee_analysis.ipynb
│   ├── 03_downtime_analysis.ipynb
│   ├── 04_predictive_maintenance.ipynb
│   ├── 05_quality_spc_analysis.ipynb
│   └── 06_root_cause_summary.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── generate_data.py
│   ├── calculate_kpis.py
│   ├── oee.py
│   ├── downtime.py
│   ├── predictive_maintenance.py
│   ├── quality.py
│   ├── spc.py
│   ├── root_cause.py
│   └── export_for_web.py
├── outputs/
│   ├── charts/
│   ├── tables/
│   └── models/
└── docs/
    ├── methodology.md
    ├── data_dictionary.md
    └── executive_summary.md
```

## How to run locally

1. Create and activate a Python 3.11+ environment.
2. Install required packages:
   pip install -r requirements.txt
3. Generate the synthetic dataset:
   python src/generate_data.py
4. Explore the notebooks in the notebooks/ folder.

## Notes

- All data in this repository is synthetic and intended for educational and portfolio purposes.
- No API keys, cloud services, or external data dependencies are required.
