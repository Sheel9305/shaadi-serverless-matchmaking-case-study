"""Summarise a results CSV as a Markdown table (one measurement label at a time).

Usage:
    python experiments/analysis/analyze_results.py                        # local results
    python experiments/analysis/analyze_results.py --input experiments/results/cloud_results.csv
    python experiments/analysis/analyze_results.py --run-id latest --write experiments/results/local_summary.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from results_schema import MEASUREMENT_LABELS, RESULTS_DIR, read_rows, single_label

COLUMNS = [
    ("scenario", "Scenario"),
    ("vus", "VUs"),
    ("requests", "Requests"),
    ("error_rate", "Error rate"),
    ("throughput_rps", "Req/s"),
    ("avg_ms", "Avg ms"),
    ("min_ms", "Min ms"),
    ("median_ms", "Median ms"),
    ("p90_ms", "p90 ms"),
    ("p95_ms", "p95 ms"),
    ("max_ms", "Max ms"),
]


def _num(value: str, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return value or "-"


def select_run(rows: list[dict], run_id: str | None) -> list[dict]:
    if not run_id:
        return rows
    if run_id == "latest":
        run_id = rows[-1]["run_id"]
    return [r for r in rows if r["run_id"] == run_id]


def to_markdown(rows: list[dict]) -> str:
    label = single_label(rows)
    rows = sorted(rows, key=lambda r: int(float(r["vus"] or 0)))
    lines = [
        f"**Measurement type: {MEASUREMENT_LABELS[label]}** (`{label}`)",
        "",
        f"Tool: {rows[0]['tool']} · Endpoint: {rows[0]['endpoint']} · Environment: {rows[0]['environment']}",
        f"Run(s): {', '.join(sorted({r['run_id'] for r in rows}))}",
        "",
        "| " + " | ".join(h for _, h in COLUMNS) + " |",
        "|" + "|".join("---:" if k not in ("scenario",) else "---" for k, _ in COLUMNS) + "|",
    ]
    for r in rows:
        cells = []
        for key, _ in COLUMNS:
            if key in ("scenario", "vus", "requests"):
                cells.append(str(r[key]))
            elif key == "error_rate":
                cells.append(f"{float(r[key]) * 100:.2f}%" if r[key] else "-")
            else:
                cells.append(_num(r[key]))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=RESULTS_DIR / "local_results.csv")
    parser.add_argument("--run-id", default="latest", help="'latest', a specific run_id, or '' for all rows")
    parser.add_argument("--write", type=Path, help="Also write the Markdown table to this file")
    args = parser.parse_args()

    rows = select_run(read_rows(args.input), args.run_id or None)
    if not rows:
        print(f"No measurement rows in {args.input}. Nothing to analyse (no results are invented).")
        return 1
    if any(r["measurement_label"] == "pending_cloud" for r in rows):
        print("Rows are 'pending_cloud' placeholders - run the AWS experiment first.")
        return 1
    markdown = to_markdown(rows)
    print(markdown)
    if args.write:
        args.write.write_text(markdown, encoding="utf-8")
        print(f"Wrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
