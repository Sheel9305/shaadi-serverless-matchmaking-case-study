"""Convert raw k6 summary JSON files into rows of the shared CSV format.

k6's ``handleSummary`` (in experiments/k6/load_test.js) writes one file per run
to ``experiments/results/raw/k6_<label>_<scenario>_<time>.json``. This script
reads them and appends rows to:

    label "local" -> experiments/results/local_results.csv  (actual_local)
    label "aws"   -> experiments/results/cloud_results.csv  (actual_aws)

Already-imported files are tracked in ``raw/.imported`` so re-running is safe.

Usage:
    python experiments/analysis/collect_results.py
    python experiments/analysis/collect_results.py --environment "AWS ap-south-1, 512 MB, x86_64"
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from results_schema import RESULTS_DIR, append_rows

LABEL_MAP = {"local": ("actual_local", "local_results.csv"), "aws": ("actual_aws", "cloud_results.csv")}


def parse_duration(value: str) -> float:
    value = str(value).strip()
    for suffix, factor in (("ms", 0.001), ("s", 1), ("m", 60), ("h", 3600)):
        if value.endswith(suffix):
            return float(value[: -len(suffix)]) * factor
    return float(value)


def k6_summary_to_row(summary: dict, source: str, environment: str, run_id: str = "") -> tuple[str, dict]:
    meta = summary.get("meta", {})
    label_key = meta.get("label", "local")
    if label_key not in LABEL_MAP:
        raise ValueError(f"{source}: unknown label {label_key!r} (expected 'local' or 'aws')")
    measurement_label, csv_name = LABEL_MAP[label_key]
    metrics = summary["metrics"]
    duration = metrics["http_req_duration"]["values"]
    reqs = metrics["http_reqs"]["values"]
    failed_rate = metrics.get("http_req_failed", {}).get("values", {}).get("rate", 0.0)
    count = int(reqs["count"])
    row = {
        "measurement_label": measurement_label,
        "run_id": run_id or Path(source).stem,
        "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "environment": environment or ("AWS (fill in region/memory)" if label_key == "aws" else "local"),
        "tool": "k6",
        "target": meta.get("base_url", ""),
        "endpoint": meta.get("endpoint", "recommendations"),
        "scenario": meta.get("scenario", ""),
        "vus": meta.get("vus", ""),
        "duration_s": parse_duration(meta.get("duration", "0s")),
        "think_time_s": meta.get("think_time_s", ""),
        "requests": count,
        "failed_requests": round(failed_rate * count),
        "error_rate": failed_rate,
        "throughput_rps": reqs.get("rate"),
        "avg_ms": duration.get("avg"),
        "min_ms": duration.get("min"),
        "median_ms": duration.get("med"),
        "max_ms": duration.get("max"),
        "p90_ms": duration.get("p(90)"),
        "p95_ms": duration.get("p(95)"),
        "p99_ms": duration.get("p(99)", ""),
        "notes": f"Imported from {Path(source).name}",
    }
    return csv_name, row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=RESULTS_DIR / "raw")
    parser.add_argument("--environment", default="", help="Describe the environment, e.g. 'AWS ap-south-1 512MB'")
    args = parser.parse_args()

    ledger = args.raw_dir / ".imported"
    done = set(ledger.read_text().split()) if ledger.exists() else set()
    files = sorted(p for p in args.raw_dir.glob("k6_*.json") if p.name not in done)
    if not files:
        print("No new k6 summary files found in", args.raw_dir)
        return 0
    # All files imported together share one run_id, so analyze/generate_charts ("--run-id latest")
    # see the whole 1/10/25/50-VU set as one run instead of only the last scenario.
    run_id = "k6-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for path in files:
        summary = json.loads(path.read_text(encoding="utf-8"))
        csv_name, row = k6_summary_to_row(summary, str(path), args.environment, run_id)
        append_rows(RESULTS_DIR / csv_name, [row])
        done.add(path.name)
        print(f"{path.name} -> {csv_name} ({row['measurement_label']}, {row['scenario']})")
    ledger.write_text("\n".join(sorted(done)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
