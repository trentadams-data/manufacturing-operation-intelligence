# Methodology

## Overview

This project uses a synthetic manufacturing data environment to demonstrate how operations analytics can translate raw machine and production signals into business insight. The analysis follows a practical workflow: generate realistic data, calculate key performance indicators, identify downtime and quality patterns, model failure risk, and summarize findings for portfolio presentation.

All results are reproducible. Data is generated from `src/generate_data.py` with a fixed random seed, and every analytics module reads the same processed CSVs and writes deterministic tables and JSON exports.

## Analytical approach

1. Data generation
   - Create deterministic synthetic records for production, maintenance, quality, and sensor behavior.
   - Inject realistic patterns such as aging machines, shift-based defect variation, and recurring downtime events.

2. KPI and OEE analysis
   - Compute throughput, yield, scrap rate, utilization, and overall equipment effectiveness.
   - Compare actual output against planned production time and ideal cycle rates.

3. Downtime analysis
   - Classify planned versus unplanned downtime.
   - Analyze downtime by machine, line, shift, reason, and severity.

4. Predictive maintenance
   - Use maintenance history and sensor readings to build a supervised failure-risk model.
   - Highlight machine conditions that are likely to drive failures or unplanned stops.

5. Quality and SPC analysis
   - Evaluate defect levels, process capability, and control-chart style signals.
   - Compare inspection results against specification limits and target values.

6. Root-cause summary
   - Combine KPI, downtime, maintenance, and quality findings into concise, portfolio-ready summaries.

## KPI methodology

KPIs are calculated from `production_runs`, joined to `products` for unit margin.

- **Scrap rate** = scrap_units / actual_units.
- **Rework rate** = rework_units / actual_units.
- **First pass yield (FPY)** = (actual_units - scrap_units - rework_units) / actual_units — the share of output that was acceptable on the first attempt.
- **Throughput per operating hour** = actual_units / (operating_minutes / 60).
- **Schedule attainment** = actual_units / planned_units.
- **Production variance** = actual_units - planned_units (reported in units and percent).
- **Estimated scrap cost** = sum(scrap_units x unit_margin). Scrap is assumed to destroy the full unit margin.
- **Estimated rework cost** = sum(rework_units x unit_margin x 0.30). Rework is recoverable, so only a fraction of the margin is treated as lost (handling, labour, partial scrap).
- **Estimated lost margin from downtime** = unplanned downtime minutes converted to forgone units using the realised throughput rate (units per operating minute), valued at the volume-weighted average unit margin.

All ratios are guarded against divide-by-zero.

## OEE calculation methodology

OEE is computed with the standard three-component model and aggregated on summed numerators and denominators within each group (so larger runs are weighted by their true time and volume contribution):

- **Availability** = operating_minutes / planned_minutes.
- **Performance** = ideal_runtime_for_actual_output / operating_time, where the ideal runtime is actual_units x ideal_cycle_time_seconds and operating time is converted to seconds.
- **Quality** = good_units / actual_units.
- **OEE** = Availability x Performance x Quality.

Safeguards and assumptions:

- Every ratio uses a divide-by-zero guard.
- Availability and Quality are clipped to [0, 1].
- Performance is also clipped to [0, 1]. Some synthetic runs beat the ideal cycle time, which would push Performance above 100%; capping at 1.0 keeps OEE interpretable as a loss model. The amount of clipping is small and is transparent in the components.
- OEE is reported at plant, production line, machine, and shift levels, plus a weekly trend (weeks smooth daily noise for charting).

## Downtime methodology

Downtime is sourced from `machine_events`, which classifies each event as planned or unplanned with a downtime duration, reason, and severity.

- Total downtime is split into planned vs unplanned minutes.
- Downtime is attributed by reason, machine, line, and shift (minutes, event count, and average minutes per event).
- A **Pareto** view sorts reasons by total minutes and reports each reason's share and cumulative share, surfacing the vital few causes that drive most loss.
- **Top recurring issues** are ranked by event frequency (not just minutes), because frequent short stops are strong candidates for standard-work fixes.

## SPC methodology

SPC uses `quality_inspections`, where each machine measures a single characteristic against a constant target and specification window. A process stream is therefore defined per machine.

For each process, an individuals (I) control chart is built using the average moving range estimate of sigma — the standard approach for individual measurements:

- sigma_hat = MR_bar / 1.128 (1.128 = d2 for a moving range of n = 2).
- Centerline = process mean.
- UCL / LCL = mean +/- 3 x sigma_hat.

Process capability uses the same within-process sigma estimate:

- **Cp** = (USL - LSL) / (6 x sigma_hat).
- **Cpk** = min(USL - mean, mean - LSL) / (3 x sigma_hat).

The module reports points outside control limits, points outside specification limits, and the count of processes below the common capability thresholds (Cpk 1.33 and 1.0). The lowest-capability process is exported as a chart-ready control chart for the website.

## Predictive maintenance methodology

A machine-day panel is built from `sensor_readings`, `machine_events`, `maintenance_logs`, and `work_centers`.

**Target.** `failure_within_7_days` is set to 1 on a machine-day if any of the following occur within the next 7 days:

- an unplanned machine event of Medium or High severity (a severe unplanned stop),
- a machine event whose reason indicates a mechanical, electrical, or sensor fault,
- a corrective maintenance action.

The final 7 days of the panel are dropped because their forward window is incomplete.

**Features.** runtime hours, 7-day rolling average temperature / vibration / pressure, 7-day alarm count, machine age, criticality, trailing 7-day downtime events, and trailing 30-day maintenance count.

**Models.** A Logistic Regression (standardized features) and a Random Forest are trained on a stratified 75/25 train/test split. Both use balanced class weights.

**Evaluation.** Accuracy, precision, recall, F1, ROC AUC, and the full confusion matrix are reported, along with Random Forest feature importance. Because a missed failure is far more costly than a false alarm, the business framing prioritizes **recall**. High-risk machines are ranked by the average predicted failure probability over the most recent two weeks.

## Root cause analysis methodology

The root-cause module reads the JSON findings produced by the OEE, downtime, quality, SPC, and predictive-maintenance modules and translates them into a single business-readable table. Each row records a finding, its likely driver, the business impact, a recommended action, a priority, and the affected area. High-priority findings are promoted into the recommendations list in the combined web export.

## Expected outcomes

The final analysis provides a credible view of how manufacturing operations intelligence can support decisions on maintenance prioritization, waste reduction, capacity planning, and quality improvement.
