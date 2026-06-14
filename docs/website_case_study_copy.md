# Manufacturing Operations Intelligence — Website Copy

Polished, website-ready copy for the portfolio case-study page. All figures are
produced by the analytics pipeline from reproducible synthetic data spanning
January–June 2025 across three plants, five production lines, and eight machines.

---

## Hero summary

**Manufacturing Operations Intelligence**
*OEE, Downtime, Quality, and Predictive Maintenance Analytics*

An end-to-end analytics case study that turns raw production, maintenance,
quality, and sensor data into the metrics plant leaders actually act on: overall
equipment effectiveness, downtime loss, quality performance, process capability,
and machine failure risk. The result is a single, decision-ready view of where
capacity is lost and what to fix first.

Headline results: **85.3% plant OEE**, **96.4% first pass yield**, **66% of
downtime unplanned**, and a Random Forest maintenance model that catches **86% of
near-term failures**.

---

## Business problem

Manufacturing leaders rarely lack data — they lack a connected view of it.
Production, maintenance, quality, and sensor systems each tell part of the story,
but the questions that drive margin sit across all of them:

- Which lines and machines are underperforming, and by how much?
- Where is downtime concentrated, and how much of it is avoidable?
- Which machines are most likely to fail in the next week?
- Which products and shifts drive the most defects and scrap?
- What is the cost of poor quality and lost availability in margin terms?

This project answers those questions in one reproducible pipeline and packages
the findings as both analyst tables and a web-ready case study.

---

## Dataset overview

The analysis runs on a synthetic but realistic manufacturing dataset across seven
related tables: production runs, machine events, maintenance logs, quality
inspections, sensor readings, products, and work centers. The data is engineered
to reflect real plant behaviour — older machines fail more often, vibration and
temperature rise ahead of failures, certain shifts carry higher defect rates, and
specific machines show recurring downtime patterns.

Scale: ~1,450 production runs, ~260 machine events, ~180 quality inspections, and
~1,250 sensor readings across eight machines and six product families.

---

## Production KPI overview

The plant produced roughly **729,000 units** across **1,448 runs** at **96.4%
first pass yield**. Schedule attainment of **88.5%** shows actual output running
about 11% below planned volume — recoverable capacity that downtime and quality
losses are consuming. Estimated cost of poor quality (scrap plus rework) totals
about **$264,000** in margin over the window, with a further **~$80,000** in
margin lost to unplanned downtime.

---

## OEE analysis

Overall equipment effectiveness is calculated with the standard model —
Availability × Performance × Quality — at plant, line, machine, and shift levels,
plus a weekly trend.

- **Plant OEE: 85.3%** (Availability 90.1%, Performance 98.2%, Quality 96.4%).
- Performance and quality are strong; **availability is the primary constraint**,
  driven by unplanned stops.
- **M-202 on Line B is the lowest-OEE asset**, and Line B is the weakest line
  overall — making it the clearest target for focused improvement.

---

## Downtime analysis

Downtime is split into planned versus unplanned and attributed by reason,
machine, line, and shift, with a Pareto view of the vital few causes.

- **66% of all downtime is unplanned** — the single biggest opportunity.
- The largest reasons are **power fluctuation, overheating, and bearing faults**,
  which together dominate total downtime minutes.
- **M-202 records the most downtime minutes**, reinforcing it as the priority
  asset for condition monitoring and reliability work.

---

## Predictive maintenance

A supervised model predicts whether each machine will experience a failure within
the next seven days, engineered from sensor trends, machine age, alarm activity,
and recent event and maintenance history.

- A **Random Forest** model achieved **recall ≈ 0.86** and **ROC AUC ≈ 0.93**,
  clearly beating Logistic Regression (recall ≈ 0.64).
- Recall is the priority metric by design: a missed failure costs far more than a
  false alarm, so the model is tuned to catch as many true failures as possible.
- The strongest predictors are **runtime hours, machine age, and rolling
  temperature**.
- **Highest-risk machines: M-302, M-202, and M-103.** M-202 appears across OEE,
  downtime, and maintenance risk — a single asset driving losses on three fronts.

---

## Quality and defect analysis

Defect rates are measured by line, machine, product family, and shift, and the
financial impact is estimated using product unit margins.

- Overall defect rate is **2.8%**, with **Line B carrying the highest rate**.
- Night shift shows elevated defects, consistent with shift-based variation.
- Estimated scrap and rework impact from inspection defect rates is **~$210,000**
  in margin, concentrated in the weakest lines and families.

---

## SPC findings

Statistical process control uses individuals control charts and capability
indices (Cp, Cpk) for each machine's measured characteristic.

- Average **Cpk ≈ 1.20**, with **seven of eight processes below the 1.33
  capability target** (none below 1.0).
- **M-102 is the least capable process** (Cpk ≈ 1.07) and is highlighted as the
  showcase control chart — marginal capability with limited headroom against the
  specification window.
- No sampled points fell outside specification limits, but the thin capability
  margin indicates real risk if processes drift.

---

## Root cause summary

The pipeline connects findings across domains into a single, business-readable
table — each with a likely driver, business impact, recommended action, priority,
and affected area. The recurring theme is clear: **availability loss and recurring
mechanical/electrical faults on a small set of aging assets** (led by M-202) are
the dominant drivers of lost capacity, while **Line B** concentrates both OEE and
quality losses.

---

## Executive recommendations

1. **Stabilize M-202 (Line B).** Lowest OEE, highest downtime, and high
   maintenance risk — prioritise a focused reliability and OEE review.
2. **Attack unplanned downtime by reason.** A Pareto-led program on power
   fluctuation, overheating, and bearing faults addresses most of the 66%
   unplanned share.
3. **Contain Line B quality losses.** Launch corrective action on the top defect
   type and investigate night-shift variation.
4. **Operationalize the maintenance watchlist.** Review the model's high-risk list
   weekly and schedule proactive inspections on M-302, M-202, and M-103.
5. **Improve marginal process capability.** Center and tighten the lowest-Cpk
   processes, starting with M-102, to build headroom against spec limits.

---

## Technical implementation

The project is a clean, reproducible Python pipeline:

- **Data**: synthetic generator with a fixed random seed for full reproducibility.
- **Analytics**: modular Python (Pandas) for KPIs, OEE, downtime, quality, and SPC.
- **Machine learning**: Scikit-learn Logistic Regression and Random Forest with a
  time-aware feature panel and recall-focused evaluation.
- **Outputs**: 18 analyst CSV tables, five Matplotlib charts, and a combined,
  frontend-friendly JSON document for the website.
- **Quality gates**: an input-validation layer plus a standalone output validator
  that checks every expected file and key field.

One command runs the entire project end to end: `python src/run_pipeline.py`.

---

## GitHub repository summary

A self-contained, dependency-light Python project demonstrating manufacturing
operations analytics from synthetic data to web-ready insight. Includes the data
generator, eight analytics modules, a one-command pipeline runner, an output
validator, generated tables and charts, and a combined case-study JSON export.
Documented methodology and reproducible results make it straightforward to read,
run, and extend.

*Dataset is synthetic and created for portfolio demonstration purposes.*
