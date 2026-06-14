"""Generate realistic synthetic manufacturing data for the portfolio project."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import MACHINE_SPECS, PRODUCTS, PROCESSED_DIR, SEED, SHIFTS, SHIFT_WEIGHTS


def _rng(seed: int = SEED) -> np.random.Generator:
    return np.random.default_rng(seed)


def _safe_float(value: float) -> float:
    return float(max(0.0, value))


def _build_products_table() -> pd.DataFrame:
    return pd.DataFrame(PRODUCTS)


def _build_work_centers_table() -> pd.DataFrame:
    return pd.DataFrame(MACHINE_SPECS)


def generate_production_runs(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    start_date = pd.Timestamp("2025-01-01")
    end_date = pd.Timestamp("2025-06-30")

    for current_date in pd.date_range(start_date, end_date, freq="D"):
        for machine in MACHINE_SPECS:
            shift = rng.choice(SHIFTS, p=list(SHIFT_WEIGHTS.values()))
            product = PRODUCTS[int(rng.integers(0, len(PRODUCTS)))]
            age = current_date.year - machine["install_year"] + (current_date.month - 1) / 12.0

            planned_minutes = float(rng.normal(420.0, 40.0))
            planned_minutes = max(180.0, min(520.0, planned_minutes))
            ideal_cycle = product["standard_cycle_time_seconds"]

            age_factor = min(1.0, age / 12.0)
            shift_factor = 1.02 if shift == "Day" else 0.98 if shift == "Swing" else 0.96
            machine_efficiency = 0.91 + 0.04 * (1.0 - age_factor) - 0.015 * (machine["criticality"] == "High")
            machine_efficiency = max(0.78, min(1.0, machine_efficiency))

            planned_units = planned_minutes * 60.0 / ideal_cycle
            actual_units = planned_units * machine_efficiency * shift_factor * (0.96 + rng.random() * 0.04)
            scrap_rate = 0.015 + 0.004 * age_factor + (0.005 if machine["criticality"] == "High" else 0.002)
            rework_rate = 0.012 + 0.002 * age_factor + (0.004 if shift == "Night" else 0.0)
            good_units = actual_units * (1.0 - scrap_rate - rework_rate)
            scrap_units = actual_units * scrap_rate
            rework_units = actual_units * rework_rate
            operating_minutes = planned_minutes * (0.84 + 0.12 * rng.random())

            rows.append(
                {
                    "run_id": f"RUN-{len(rows)+1:05d}",
                    "date": current_date,
                    "plant": machine["plant"],
                    "production_line": machine["production_line"],
                    "machine_id": machine["machine_id"],
                    "product_id": product["product_id"],
                    "shift": shift,
                    "planned_minutes": round(planned_minutes, 1),
                    "operating_minutes": round(operating_minutes, 1),
                    "ideal_cycle_time_seconds": round(ideal_cycle, 2),
                    "planned_units": round(planned_units, 1),
                    "actual_units": round(actual_units, 1),
                    "good_units": round(good_units, 1),
                    "scrap_units": round(scrap_units, 1),
                    "rework_units": round(rework_units, 1),
                    "operator_team": rng.choice(["Team A", "Team B", "Team C", "Team D"]),
                }
            )

    return pd.DataFrame(rows)


def generate_machine_events(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    reasons = {
        "planned": ["planned maintenance", "calibration", "scheduled inspection", "tool change"],
        "unplanned": ["belt wear", "sensor drift", "lubrication issue", "bearing fault", "overheat", "power fluctuation"],
    }

    for idx, machine in enumerate(MACHINE_SPECS, start=1):
        for day_offset in range(0, 180, 3):
            if rng.random() < 0.55:
                event_type = "planned" if rng.random() < 0.35 else "unplanned"
                reason = rng.choice(reasons[event_type])
                age_factor = max(0.0, (2025 - machine["install_year"]) / 10.0)
                downtime_minutes = _safe_float(rng.gamma(shape=2.2 + age_factor, scale=8.0))
                severity = "Low"
                if event_type == "unplanned" and (machine["criticality"] == "High" or age_factor > 0.5):
                    severity = rng.choice(["Medium", "High"])
                elif event_type == "planned":
                    severity = "Low"

                rows.append(
                    {
                        "event_id": f"EVT-{len(rows)+1:05d}",
                        "date": pd.Timestamp("2025-01-01") + pd.Timedelta(days=day_offset + idx % 5),
                        "production_line": machine["production_line"],
                        "machine_id": machine["machine_id"],
                        "shift": rng.choice(SHIFTS),
                        "event_type": event_type,
                        "downtime_reason": reason,
                        "downtime_minutes": round(downtime_minutes, 1),
                        "severity": severity,
                    }
                )

    return pd.DataFrame(rows)


def generate_maintenance_logs(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    maintenance_types = ["preventive", "corrective", "inspection", "replacement"]

    for machine in MACHINE_SPECS:
        for month in range(1, 7):
            if rng.random() < 0.6:
                maintenance_type = rng.choice(maintenance_types)
                age_factor = max(0.0, (2025 - machine["install_year"]) / 10.0)
                maintenance_minutes = _safe_float(rng.normal(90.0 + age_factor * 60.0, 22.0))
                cost = round(120.0 + age_factor * 180.0 + maintenance_minutes * 0.8, 2)
                issue_found = "Bearing lubrication" if maintenance_type == "preventive" else "Sensor drift"
                if machine["machine_id"] in {"M-101", "M-202"}:
                    issue_found = "Repeated vibration spike"

                rows.append(
                    {
                        "maintenance_id": f"MTN-{len(rows)+1:05d}",
                        "date": pd.Timestamp(f"2025-{month:02d}-15"),
                        "machine_id": machine["machine_id"],
                        "maintenance_type": maintenance_type,
                        "maintenance_minutes": round(maintenance_minutes, 1),
                        "component": rng.choice(["Motor", "Belt", "Sensor", "Hydraulic", "Control Board"]),
                        "issue_found": issue_found,
                        "cost": cost,
                    }
                )

    return pd.DataFrame(rows)


def generate_quality_inspections(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    defect_types = ["surface scratch", "dimensional drift", "seal leak", "misalignment", "contamination"]

    for idx, machine in enumerate(MACHINE_SPECS):
        for day_offset in range(0, 120, 3):
            if rng.random() < 0.55:
                product = PRODUCTS[int(rng.integers(0, len(PRODUCTS)))]
                shift = rng.choice(SHIFTS)
                sample_size = int(rng.integers(25, 100))
                defect_rate = 0.02 + 0.012 * (machine["criticality"] == "High") + (0.01 if shift == "Night" else 0.0)
                defect_count = int(round(rng.binomial(sample_size, defect_rate)))
                target_value = 12.5 + (idx % 3) * 0.3
                measurement_value = target_value + rng.normal(0.0, 0.25)
                lower_spec = target_value - 1.0
                upper_spec = target_value + 1.0

                rows.append(
                    {
                        "inspection_id": f"INS-{len(rows)+1:05d}",
                        "date": pd.Timestamp("2025-01-01") + pd.Timedelta(days=day_offset),
                        "production_line": machine["production_line"],
                        "machine_id": machine["machine_id"],
                        "product_id": product["product_id"],
                        "shift": shift,
                        "sample_size": sample_size,
                        "defect_count": defect_count,
                        "defect_type": rng.choice(defect_types),
                        "measurement_value": round(measurement_value, 3),
                        "target_value": round(target_value, 3),
                        "lower_spec_limit": round(lower_spec, 3),
                        "upper_spec_limit": round(upper_spec, 3),
                    }
                )

    return pd.DataFrame(rows)


def generate_sensor_readings(rng: np.random.Generator) -> pd.DataFrame:
    rows = []

    for machine in MACHINE_SPECS:
        age_factor = max(0.0, (2025 - machine["install_year"]) / 10.0)
        start_time = pd.Timestamp("2025-01-01 00:00:00")
        for hour_step in range(0, 1440, 6):
            if rng.random() < 0.35:
                continue
            timestamp = start_time + pd.Timedelta(hours=hour_step + (idx := MACHINE_SPECS.index(machine)) * 2)
            temperature = 58.0 + age_factor * 9.0 + rng.normal(0.0, 3.0) + (1.5 if rng.random() < 0.15 else 0.0)
            vibration = 1.8 + age_factor * 0.6 + rng.normal(0.0, 0.25)
            pressure = 5.8 + rng.normal(0.0, 0.25)
            runtime_hours = max(0.0, 120.0 + hour_step / 24.0 + age_factor * 90.0)
            alarm_count = 0
            if vibration > 2.4 or temperature > 68.0:
                alarm_count = int(rng.integers(1, 4))

            rows.append(
                {
                    "reading_id": f"RDG-{len(rows)+1:05d}",
                    "timestamp": timestamp,
                    "machine_id": machine["machine_id"],
                    "temperature_c": round(temperature, 2),
                    "vibration_mm_s": round(vibration, 2),
                    "pressure_bar": round(pressure, 2),
                    "runtime_hours": round(runtime_hours, 1),
                    "alarm_count": alarm_count,
                }
            )

    return pd.DataFrame(rows)


def write_processed_tables() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rng = _rng()

    tables = {
        "production_runs.csv": generate_production_runs(rng),
        "machine_events.csv": generate_machine_events(rng),
        "maintenance_logs.csv": generate_maintenance_logs(rng),
        "quality_inspections.csv": generate_quality_inspections(rng),
        "sensor_readings.csv": generate_sensor_readings(rng),
        "products.csv": _build_products_table(),
        "work_centers.csv": _build_work_centers_table(),
    }

    for filename, frame in tables.items():
        (PROCESSED_DIR / filename).write_text(frame.to_csv(index=False), encoding="utf-8")

    print(f"Synthetic data written to {PROCESSED_DIR}")
    for name in tables:
        print(f" - {name}: {len(tables[name])} rows")


def main() -> None:
    write_processed_tables()


if __name__ == "__main__":
    main()
