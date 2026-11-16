"""Shared result format and statistics for all experiment scripts.

Every row in a results CSV MUST carry exactly one ``measurement_label``:

    actual_local   - measured by us on a laptop against the local API
    actual_aws     - measured by us against the deployed AWS API
    pending_cloud  - placeholder row: AWS measurement not yet collected
    illustrative   - example numbers for explaining the method (never results)

Scripts refuse to mix labels in one table or chart.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Iterable, Sequence
from pathlib import Path

MEASUREMENT_LABELS = {
    "actual_local": "Actual local measurement",
    "actual_aws": "Actual AWS measurement",
    "pending_cloud": "Pending cloud measurement",
    "illustrative": "Illustrative example",
}

CSV_COLUMNS = [
    "measurement_label",
    "run_id",
    "timestamp_utc",
    "environment",
    "tool",
    "target",
    "endpoint",
    "scenario",
    "vus",
    "duration_s",
    "think_time_s",
    "requests",
    "failed_requests",
    "error_rate",
    "throughput_rps",
    "avg_ms",
    "min_ms",
    "median_ms",
    "max_ms",
    "p90_ms",
    "p95_ms",
    "p99_ms",
    "notes",
]

EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXPERIMENTS_DIR / "results"
CHARTS_DIR = EXPERIMENTS_DIR / "charts"


def percentile(sorted_values: Sequence[float], pct: float) -> float:
    """Linear-interpolation percentile (same method as numpy's default)."""
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (pct / 100) * (len(sorted_values) - 1)
    low, high = math.floor(rank), math.ceil(rank)
    fraction = rank - low
    return float(sorted_values[low] + (sorted_values[high] - sorted_values[low]) * fraction)


def summarise(latencies_ms: Iterable[float]) -> dict[str, float]:
    values = sorted(latencies_ms)
    if not values:
        return {k: math.nan for k in ("avg_ms", "min_ms", "median_ms", "max_ms", "p90_ms", "p95_ms", "p99_ms")}
    return {
        "avg_ms": sum(values) / len(values),
        "min_ms": values[0],
        "median_ms": percentile(values, 50),
        "max_ms": values[-1],
        "p90_ms": percentile(values, 90),
        "p95_ms": percentile(values, 95),
        "p99_ms": percentile(values, 99),
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [row for row in csv.DictReader(fh) if row.get("measurement_label")]


def append_rows(path: Path, rows: list[dict]) -> None:
    for row in rows:
        if row.get("measurement_label") not in MEASUREMENT_LABELS:
            raise ValueError(f"Invalid measurement_label: {row.get('measurement_label')!r}")
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: _fmt(row.get(k, "")) for k in CSV_COLUMNS})


def _fmt(value):
    if isinstance(value, float):
        return "" if math.isnan(value) else f"{value:.3f}"
    return value


def single_label(rows: list[dict[str, str]]) -> str:
    labels = {r["measurement_label"] for r in rows}
    if len(labels) != 1:
        raise ValueError(f"Refusing to mix measurement labels in one analysis: {sorted(labels)}")
    return labels.pop()
