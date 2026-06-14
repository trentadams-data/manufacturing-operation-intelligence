"""Predictive maintenance modelling.

Builds a machine-day panel from sensor readings, machine events, and maintenance
logs, engineers a ``failure_within_7_days`` target, and trains two classifiers
(Logistic Regression and Random Forest). The business cost of a missed failure
far exceeds that of a false alarm, so both models use balanced class weights and
the evaluation emphasises **recall**.

Target definition -- a failure is flagged on a machine-day if any of the
following occur within the next 7 days:

* an unplanned machine event of Medium or High severity (severe unplanned stop),
* a machine event whose reason indicates a mechanical / electrical / sensor fault,
* a corrective maintenance action.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import SEED
from src.data_io import PipelineError, load_required, r, write_json, write_table

FAILURE_HORIZON_DAYS = 7
FORECAST_WINDOW = pd.Timedelta(days=FAILURE_HORIZON_DAYS)

CRITICALITY_CODE = {"Low": 0, "Medium": 1, "High": 2}

# Reasons that represent genuine mechanical / electrical / sensor faults rather
# than routine planned stops.
FAULT_REASONS = {
    "bearing fault",
    "overheat",
    "power fluctuation",
    "sensor drift",
    "lubrication issue",
    "belt wear",
}

FEATURE_COLUMNS = [
    "runtime_hours",
    "roll_temp_7",
    "roll_vibration_7",
    "roll_pressure_7",
    "alarm_count_7",
    "machine_age_years",
    "criticality_code",
    "downtime_events_7",
    "maintenance_count_30",
]


def create_risk_signal(sensor_readings: pd.DataFrame) -> pd.DataFrame:
    """Create a simple heuristic risk score (kept for notebook compatibility)."""
    if sensor_readings.empty:
        return sensor_readings.copy()

    sensor_readings = sensor_readings.copy()
    sensor_readings["risk_score"] = (
        0.35 * (sensor_readings["temperature_c"] / 80.0)
        + 0.40 * (sensor_readings["vibration_mm_s"] / 4.0)
        + 0.25 * (sensor_readings["alarm_count"] / 3.0)
    )
    return sensor_readings


def _failure_dates(machine_events: pd.DataFrame, maintenance_logs: pd.DataFrame) -> dict[str, np.ndarray]:
    """Return sorted failure dates per machine from events and corrective work."""
    severe = machine_events[
        (
            (machine_events["event_type"] == "unplanned")
            & machine_events["severity"].isin(["Medium", "High"])
        )
        | (machine_events["downtime_reason"].isin(FAULT_REASONS))
    ][["machine_id", "date"]]

    corrective = maintenance_logs[maintenance_logs["maintenance_type"] == "corrective"][
        ["machine_id", "date"]
    ]

    failures = pd.concat([severe, corrective], ignore_index=True)
    return {
        machine_id: np.sort(group["date"].values)
        for machine_id, group in failures.groupby("machine_id")
    }


def build_panel(
    sensor_readings: pd.DataFrame,
    machine_events: pd.DataFrame,
    maintenance_logs: pd.DataFrame,
    work_centers: pd.DataFrame,
) -> pd.DataFrame:
    """Construct the machine-day feature/target panel for modelling."""
    sensors = sensor_readings.copy()
    sensors["date"] = sensors["timestamp"].dt.normalize()
    daily = (
        sensors.groupby(["machine_id", "date"])
        .agg(
            temperature_c=("temperature_c", "mean"),
            vibration_mm_s=("vibration_mm_s", "mean"),
            pressure_bar=("pressure_bar", "mean"),
            runtime_hours=("runtime_hours", "max"),
            alarm_count=("alarm_count", "sum"),
        )
        .reset_index()
    )

    full_dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    events_idx = machine_events.set_index("date")
    maint_idx = maintenance_logs.set_index("date")
    failure_lookup = _failure_dates(machine_events, maintenance_logs)

    panels = []
    for machine_id, group in daily.groupby("machine_id"):
        # Reindex onto a continuous daily calendar and carry sensor state forward
        # (sensors are sampled intermittently in the source data).
        panel = (
            group.set_index("date")
            .reindex(full_dates)
            .ffill()
            .bfill()
            .rename_axis("date")
            .reset_index()
        )
        panel["machine_id"] = machine_id

        # Rolling condition features (trailing 7 days, min_periods=1 to keep the
        # earliest rows usable).
        panel["roll_temp_7"] = panel["temperature_c"].rolling(7, min_periods=1).mean()
        panel["roll_vibration_7"] = panel["vibration_mm_s"].rolling(7, min_periods=1).mean()
        panel["roll_pressure_7"] = panel["pressure_bar"].rolling(7, min_periods=1).mean()
        panel["alarm_count_7"] = panel["alarm_count"].rolling(7, min_periods=1).sum()

        # Trailing event / maintenance counts.
        machine_events_daily = (
            events_idx[events_idx["machine_id"] == machine_id]
            .groupby(level=0)
            .size()
            .reindex(full_dates, fill_value=0)
        )
        panel["downtime_events_7"] = (
            machine_events_daily.rolling(7, min_periods=1).sum().to_numpy()
        )
        machine_maint_daily = (
            maint_idx[maint_idx["machine_id"] == machine_id]
            .groupby(level=0)
            .size()
            .reindex(full_dates, fill_value=0)
        )
        panel["maintenance_count_30"] = (
            machine_maint_daily.rolling(30, min_periods=1).sum().to_numpy()
        )

        # Machine attributes.
        spec = work_centers[work_centers["machine_id"] == machine_id].iloc[0]
        install = pd.Timestamp(year=int(spec["install_year"]), month=1, day=1)
        panel["machine_age_years"] = (panel["date"] - install).dt.days / 365.25
        panel["criticality"] = spec["criticality"]
        panel["criticality_code"] = CRITICALITY_CODE.get(spec["criticality"], 1)

        # Forward-looking target.
        failure_days = failure_lookup.get(machine_id, np.array([], dtype="datetime64[ns]"))
        panel["failure_within_7_days"] = panel["date"].apply(
            lambda d: _has_future_failure(d, failure_days)
        )

        panels.append(panel)

    combined = pd.concat(panels, ignore_index=True)
    # Drop the final horizon where the forward window is incomplete (would bias
    # the target toward 0) and any rows still missing engineered features.
    cutoff = full_dates.max() - FORECAST_WINDOW
    combined = combined[combined["date"] <= cutoff]
    combined = combined.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    return combined


def _has_future_failure(day: pd.Timestamp, failure_days: np.ndarray) -> int:
    """Return 1 if a failure occurs in (day, day + horizon]."""
    if failure_days.size == 0:
        return 0
    window_end = day + FORECAST_WINDOW
    in_window = (failure_days > np.datetime64(day)) & (
        failure_days <= np.datetime64(window_end)
    )
    return int(in_window.any())


def _evaluate(name: str, model, X_test, y_test) -> dict[str, float]:
    """Score a fitted model on the held-out set."""
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
    return {
        "model": name,
        "accuracy": r(accuracy_score(y_test, predictions), 4),
        "precision": r(precision_score(y_test, predictions, zero_division=0), 4),
        "recall": r(recall_score(y_test, predictions, zero_division=0), 4),
        "f1": r(f1_score(y_test, predictions, zero_division=0), 4),
        "roc_auc": r(roc_auc_score(y_test, probabilities), 4),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }


def run() -> dict[str, object]:
    """Build the panel, train and evaluate both models, and write outputs."""
    sensor_readings = load_required(
        "sensor_readings",
        [
            "machine_id",
            "timestamp",
            "temperature_c",
            "vibration_mm_s",
            "pressure_bar",
            "runtime_hours",
            "alarm_count",
        ],
    )
    machine_events = load_required(
        "machine_events",
        ["machine_id", "date", "event_type", "downtime_reason", "severity"],
    )
    maintenance_logs = load_required(
        "maintenance_logs", ["machine_id", "date", "maintenance_type"]
    )
    work_centers = load_required(
        "work_centers", ["machine_id", "install_year", "criticality"]
    )

    panel = build_panel(sensor_readings, machine_events, maintenance_logs, work_centers)
    if panel.empty:
        raise PipelineError(
            "Predictive-maintenance panel is empty after feature engineering; "
            "check the sensor and event date ranges."
        )

    X = panel[FEATURE_COLUMNS]
    y = panel["failure_within_7_days"].astype(int)

    positive_rate = float(y.mean())
    if y.nunique() < 2:
        raise PipelineError(
            "Engineered target 'failure_within_7_days' has a single class; "
            "cannot train classifiers."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )

    logistic = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=1000, class_weight="balanced", random_state=SEED
                ),
            ),
        ]
    )
    forest = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )

    logistic.fit(X_train, y_train)
    forest.fit(X_train, y_train)

    results = [
        _evaluate("Logistic Regression", logistic, X_test, y_test),
        _evaluate("Random Forest", forest, X_test, y_test),
    ]
    results_table = pd.DataFrame(results)
    write_table(results_table, "predictive_maintenance_model_results.csv")

    # Feature importance from the Random Forest.
    importance = (
        pd.DataFrame(
            {"feature": FEATURE_COLUMNS, "importance": forest.feature_importances_}
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    importance["importance"] = importance["importance"].round(4)
    write_table(importance, "feature_importance.csv")

    # High-risk machines: average the Random Forest failure probability over the
    # most recent two weeks of each machine's panel (recall-oriented monitoring).
    panel = panel.copy()
    panel["risk_probability"] = forest.predict_proba(X)[:, 1]
    recent_cutoff = panel["date"].max() - pd.Timedelta(days=14)
    recent = panel[panel["date"] >= recent_cutoff]
    high_risk = (
        recent.groupby("machine_id")
        .agg(
            avg_risk_probability=("risk_probability", "mean"),
            latest_runtime_hours=("runtime_hours", "max"),
            avg_vibration=("roll_vibration_7", "mean"),
            avg_temperature=("roll_temp_7", "mean"),
            criticality=("criticality", "first"),
            machine_age_years=("machine_age_years", "max"),
        )
        .reset_index()
        .sort_values("avg_risk_probability", ascending=False)
        .reset_index(drop=True)
    )
    for column in [
        "avg_risk_probability",
        "latest_runtime_hours",
        "avg_vibration",
        "avg_temperature",
        "machine_age_years",
    ]:
        high_risk[column] = high_risk[column].round(3)
    high_risk["risk_tier"] = pd.cut(
        high_risk["avg_risk_probability"],
        bins=[-0.01, 0.34, 0.66, 1.01],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    write_table(high_risk, "high_risk_machines.csv")

    best_recall = max(results, key=lambda row: row["recall"])
    summary = {
        "panel_rows": int(len(panel)),
        "feature_count": len(FEATURE_COLUMNS),
        "target": "failure_within_7_days",
        "positive_rate": r(positive_rate, 4),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "model_results": results,
        "recommended_model": best_recall["model"],
        "recommended_model_recall": best_recall["recall"],
        "feature_importance": importance.to_dict(orient="records"),
        "high_risk_machines": high_risk.to_dict(orient="records"),
    }
    write_json(summary, "predictive_maintenance_results.json")
    write_json(high_risk.to_dict(orient="records"), "high_risk_machines.json")

    print(
        f"PM panel: {len(panel)} rows, positive rate {positive_rate:.2%}. "
        f"Best recall: {best_recall['model']} ({best_recall['recall']}). "
        f"Top risk machine: {high_risk.iloc[0]['machine_id']}"
    )
    return summary


def main() -> None:
    run()


if __name__ == "__main__":
    main()
