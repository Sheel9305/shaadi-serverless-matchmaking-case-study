"""Generate charts ONLY from real measurements (actual_local or actual_aws).

Placeholder (pending_cloud) and illustrative rows are refused, so a chart can
never show invented numbers. Each chart's title states its measurement type.

Usage:
    python experiments/analysis/generate_charts.py
    python experiments/analysis/generate_charts.py --input experiments/results/cloud_results.csv --prefix aws
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from analyze_results import select_run  # noqa: E402
from results_schema import CHARTS_DIR, MEASUREMENT_LABELS, RESULTS_DIR, read_rows, single_label  # noqa: E402

ALLOWED = {"actual_local", "actual_aws"}
PALETTE = {"avg": "#8a2c4f", "median": "#c98a1b", "p90": "#2b6cb0", "p95": "#1f7a4d"}


def _style(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=11, loc="left")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)


def make_charts(rows: list[dict], out_dir: Path, prefix: str) -> list[Path]:
    label = single_label(rows)
    if label not in ALLOWED:
        raise SystemExit(f"Refusing to chart '{label}' rows - charts are only made from actual measurements.")
    tag = MEASUREMENT_LABELS[label]
    rows = sorted(rows, key=lambda r: int(float(r["vus"])))
    vus = [int(float(r["vus"])) for r in rows]
    xs = list(range(len(vus)))
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    fig, ax = plt.subplots(figsize=(7, 4))
    for key, col in (("avg", "avg_ms"), ("median", "median_ms"), ("p90", "p90_ms"), ("p95", "p95_ms")):
        ax.plot(xs, [float(r[col]) for r in rows], marker="o", label=key, color=PALETTE[key], linewidth=2)
    ax.set_xticks(xs, [str(v) for v in vus])
    _style(ax, f"Latency vs concurrency — {tag}", "Virtual users", "Latency (ms)")
    ax.legend(frameon=False)
    fig.text(0.01, 0.01, f"POST /recommendations · {rows[0]['tool']} · run {rows[0]['run_id']}", fontsize=7, alpha=0.7)
    fig.tight_layout()
    p = out_dir / f"{prefix}_latency_vs_vus.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(xs, [float(r["throughput_rps"]) for r in rows], color="#8a2c4f", width=0.55)
    ax.bar_label(bars, fmt="%.1f", fontsize=8)
    ax.set_xticks(xs, [str(v) for v in vus])
    _style(ax, f"Throughput vs concurrency — {tag}", "Virtual users", "Requests per second")
    fig.tight_layout()
    p = out_dir / f"{prefix}_throughput_vs_vus.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.25
    for i, (key, col) in enumerate((("min", "min_ms"), ("p95", "p95_ms"), ("max", "max_ms"))):
        ax.bar(
            [x + (i - 1) * width for x in xs],
            [float(r[col]) for r in rows],
            width,
            label=key,
            color=["#c98a1b", "#1f7a4d", "#b3261e"][i],
        )
    ax.set_xticks(xs, [str(v) for v in vus])
    _style(ax, f"Min / p95 / max latency — {tag}", "Virtual users", "Latency (ms)")
    ax.legend(frameon=False)
    fig.tight_layout()
    p = out_dir / f"{prefix}_latency_spread.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=RESULTS_DIR / "local_results.csv")
    parser.add_argument("--run-id", default="latest")
    parser.add_argument("--prefix", default="local")
    parser.add_argument("--out-dir", type=Path, default=CHARTS_DIR)
    args = parser.parse_args()
    rows = select_run(read_rows(args.input), args.run_id or None)
    if not rows:
        print(f"No measurement rows in {args.input}; no charts generated.")
        return 1
    for path in make_charts(rows, args.out_dir, args.prefix):
        print("Wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
