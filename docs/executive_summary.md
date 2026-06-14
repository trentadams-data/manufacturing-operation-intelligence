# Executive Summary

This project presents a synthetic manufacturing operations intelligence case study for a portfolio website. It combines production, maintenance, quality, and sensor data to tell a realistic story about line performance, reliability, and process health, and turns those signals into business language: throughput, downtime loss, maintenance risk, defect performance, and process stability.

All figures below are produced by the analytics pipeline (`python -m src.export_for_web`) from reproducible synthetic data spanning January–June 2025 across three plants, five production lines, and eight machines. The numbers are illustrative of the type of findings the analysis surfaces.

## Headline performance

- **Plant OEE: 85.3%** — Availability 90.1%, Performance 98.2%, Quality 96.4%. Performance is strong; availability loss from unplanned stops is the main constraint.
- **First pass yield: 96.4%**, with a scrap rate of 2.2% and rework rate of 1.4% across ~729,000 units produced in 1,448 runs.
- **Schedule attainment: 88.5%** — actual output ran roughly 11% below planned volume, indicating recoverable capacity.

## Cost of poor quality and downtime

- **Estimated scrap cost: ~$220,000** and **estimated rework cost: ~$44,000** over the period (valued at product unit margin).
- **Estimated margin lost to unplanned downtime: ~$80,000**, derived from ~72 operating hours of unplanned stops converted to forgone output.
- **Estimated total quality impact (scrap + rework from inspection defect rates): ~$210,000.**

## Where the losses concentrate

- **Lowest-OEE asset: M-202** (OEE 83.5%), on Line B — also the worst-performing line overall.
- **Downtime: 66% of all downtime is unplanned.** The largest single reason is **power fluctuation**, and **M-202** is the worst machine for downtime minutes. The most frequent recurring stops are power fluctuation, overheating, and bearing faults.
- **Quality: Line B has the highest defect rate**, and the most common defect type drives a disproportionate share of inspection defects. Night shift shows elevated defect rates consistent with the simulated shift pattern.

## Process capability (SPC)

- Average **Cpk ≈ 1.20** across the eight machine processes, with **seven of eight processes below the 1.33 capability target** but none below 1.0.
- **M-102** is the least capable process (Cpk ≈ 1.07) and is exported as the showcase control chart. No measurement points fell outside specification limits in the sample, but the marginal capability indicates limited headroom against the spec window.

## Predictive maintenance

- A **Random Forest** model predicting `failure_within_7_days` achieved **recall ≈ 0.86** and **ROC AUC ≈ 0.93** on the held-out set, clearly outperforming Logistic Regression (recall ≈ 0.64). Recall is the priority metric because a missed failure is far more costly than a false alarm.
- The strongest predictors are **runtime hours, machine age, and rolling temperature**, followed by pressure and vibration.
- **Highest-risk machines: M-302, M-202, and M-103** — all flagged High risk. M-202 appears across OEE, downtime, and maintenance risk, making it the clearest single target for intervention.

## Recommended actions

1. **Stabilize M-202 (Line B).** It is simultaneously the lowest-OEE, highest-downtime, and a high-maintenance-risk asset — prioritize a focused reliability and OEE review.
2. **Attack unplanned downtime by reason.** Power fluctuation, overheating, and bearing faults dominate; a Pareto-led program targeting the top reasons addresses most of the 66% unplanned share.
3. **Contain Line B quality losses.** Stand up a corrective-action plan for the top defect type and investigate night-shift variation.
4. **Operationalize the maintenance watchlist.** Review the Random Forest high-risk list weekly and schedule proactive inspections on M-302, M-202, and M-103.
5. **Improve marginal process capability.** Center and tighten the lowest-Cpk processes (starting with M-102) to build headroom against specification limits.

The project is intentionally lightweight, reproducible, and suitable for portfolio presentation without any external services or paid dependencies.
