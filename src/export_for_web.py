"""Utilities for web-ready export artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import WEB_EXPORT_DIR


def export_summary(summary: dict[str, object], filename: str = "portfolio_summary.json") -> None:
    """Write summary data to the web export folder."""
    WEB_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = WEB_EXPORT_DIR / filename
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Exported summary to {output_path}")


def export_table(frame: pd.DataFrame, filename: str) -> None:
    """Write a table to the web export folder."""
    WEB_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    (WEB_EXPORT_DIR / filename).write_text(frame.to_csv(index=False), encoding="utf-8")
