"""Shared helpers for loading processed tables and writing analytics outputs.

Every analytics module reads the same synthetic CSVs from ``data/processed`` and
writes tables to ``outputs/tables`` and web-ready JSON to ``data/web_exports``.
Centralising that logic here keeps the individual modules focused on analysis and
guarantees consistent date parsing, rounding, and JSON serialisation.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import OUTPUTS_DIR, PROCESSED_DIR, WEB_EXPORT_DIR

TABLES_DIR = OUTPUTS_DIR / "tables"
CHARTS_DIR = OUTPUTS_DIR / "charts"
MODELS_DIR = OUTPUTS_DIR / "models"

# Columns that should be parsed as dates/timestamps when a table is loaded.
_DATE_COLUMNS = {
    "production_runs": ["date"],
    "machine_events": ["date"],
    "maintenance_logs": ["date"],
    "quality_inspections": ["date"],
    "sensor_readings": ["timestamp"],
}


class PipelineError(RuntimeError):
    """Raised when a processed table is missing, empty, or malformed.

    Carries a clear, user-facing message so the pipeline runner can fail with an
    actionable error instead of a deep stack trace.
    """


def ensure_not_empty(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    """Raise :class:`PipelineError` if a loaded table has no rows."""
    if frame is None or frame.empty:
        raise PipelineError(
            f"Table '{name}' is empty. Re-run `python src/generate_data.py`."
        )
    return frame


def require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> pd.DataFrame:
    """Raise :class:`PipelineError` if any expected column is missing."""
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise PipelineError(
            f"Table '{name}' is missing required column(s): {', '.join(missing)}."
        )
    return frame


def ensure_output_dirs() -> None:
    """Create every output directory used by the analytics pipeline."""
    for directory in (TABLES_DIR, CHARTS_DIR, MODELS_DIR, WEB_EXPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def load_table(name: str) -> pd.DataFrame:
    """Load a single processed CSV by stem name (e.g. ``"production_runs"``)."""
    path = PROCESSED_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Expected processed table '{path}'. Run `python src/generate_data.py` first."
        )
    frame = pd.read_csv(path)
    for column in _DATE_COLUMNS.get(name, []):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def load_required(name: str, columns: list[str]) -> pd.DataFrame:
    """Load a processed table and validate it is non-empty with required columns.

    Combines the three most common failure checks (missing file, empty table,
    missing columns) into one call so each analytics module stays readable.
    """
    frame = load_table(name)
    ensure_not_empty(frame, name)
    require_columns(frame, columns, name)
    return frame


def load_all() -> dict[str, pd.DataFrame]:
    """Load every processed table into a dictionary keyed by table name."""
    names = [
        "production_runs",
        "machine_events",
        "maintenance_logs",
        "quality_inspections",
        "sensor_readings",
        "products",
        "work_centers",
    ]
    return {name: load_table(name) for name in names}


def write_table(frame: pd.DataFrame, filename: str) -> Path:
    """Write a dataframe to ``outputs/tables`` as CSV and return the path."""
    ensure_output_dirs()
    path = TABLES_DIR / filename
    try:
        frame.to_csv(path, index=False)
    except OSError as error:
        raise PipelineError(f"Could not write table '{path}': {error}") from error
    return path


def _json_default(value: Any) -> Any:
    """JSON serialiser fallback for numpy / pandas / NaN values."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if math.isnan(float(value)) else float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serialisable")


def write_json(obj: Any, filename: str) -> Path:
    """Write an object to ``data/web_exports`` as nicely formatted JSON."""
    ensure_output_dirs()
    path = WEB_EXPORT_DIR / filename
    try:
        path.write_text(json.dumps(obj, indent=2, default=_json_default), encoding="utf-8")
    except OSError as error:
        raise PipelineError(f"Could not write JSON '{path}': {error}") from error
    return path


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a dataframe to JSON-friendly records (NaN -> None, dates -> str)."""
    cleaned = frame.copy()
    for column in cleaned.columns:
        if pd.api.types.is_datetime64_any_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].dt.strftime("%Y-%m-%d")
    cleaned = cleaned.where(pd.notnull(cleaned), None)
    return cleaned.to_dict(orient="records")


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide two numbers, returning ``default`` when the denominator is ~zero."""
    if denominator is None or abs(float(denominator)) < 1e-9:
        return default
    return float(numerator) / float(denominator)


def r(value: float, digits: int = 2) -> float:
    """Round a numeric value, returning ``0.0`` for NaN/None for clean JSON."""
    if value is None:
        return 0.0
    value = float(value)
    if math.isnan(value):
        return 0.0
    return round(value, digits)
