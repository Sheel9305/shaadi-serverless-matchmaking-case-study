"""Closed-loop concurrency benchmark written in Python (fallback when k6 is not installed).

It imitates k6's ``constant-vus`` executor: N virtual users (threads) each send
a request, wait for the response, sleep ``think_time`` seconds, and repeat until
the scenario duration ends. Latency is measured on the client with
``time.perf_counter`` (request sent -> full response received).

Results are labelled ``actual_local`` and appended to
``experiments/results/local_results.csv``; raw per-request samples go to
``experiments/results/raw/``. Use the k6 scripts for the AWS experiment.

Usage (API must already be running, e.g. via experiments/run_local_experiments.sh):
    python experiments/run_local_benchmark.py --base-url http://127.0.0.1:8000
    python experiments/run_local_benchmark.py --scenarios vu1 vu10 --duration 10
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent / "analysis"))
from results_schema import RESULTS_DIR, append_rows, summarise  # noqa: E402

CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "scenarios.json"

PROFILES = [
    {
        "user_id": "U001",
        "age": 25,
        "city": "Ahmedabad",
        "education": "Engineering",
        "interests": ["music", "travel", "technology"],
        "preferences": {"min_age": 23, "max_age": 29, "preferred_city": "Ahmedabad"},
    },
    {
        "user_id": "U002",
        "age": 30,
        "city": "Mumbai",
        "education": "Commerce",
        "interests": ["movies", "cooking", "fitness"],
        "preferences": {"min_age": 26, "max_age": 34, "preferred_city": "Mumbai"},
    },
    {
        "user_id": "U003",
        "age": 28,
        "city": "Pune",
        "education": "Science",
        "interests": ["reading", "hiking"],
        "preferences": {"min_age": 24, "max_age": 34},
    },
]


def run_scenario(base_url: str, vus: int, duration_s: float, think_time_s: float) -> dict:
    url = f"{base_url.rstrip('/')}/recommendations"
    deadline = time.perf_counter() + duration_s
    latencies: list[float] = []
    failures = 0
    lock = threading.Lock()

    def virtual_user(vu_id: int) -> None:
        nonlocal failures
        iteration = 0
        with httpx.Client(timeout=10.0) as client:
            while time.perf_counter() < deadline:
                body = PROFILES[(vu_id + iteration) % len(PROFILES)]
                start = time.perf_counter()
                ok = False
                try:
                    response = client.post(url, json=body)
                    ok = response.status_code == 200 and "recommendations" in response.json()
                except httpx.HTTPError:
                    ok = False
                elapsed_ms = (time.perf_counter() - start) * 1000
                with lock:
                    latencies.append(elapsed_ms)
                    if not ok:
                        failures += 1
                iteration += 1
                if think_time_s:
                    time.sleep(think_time_s)

    started = time.perf_counter()
    threads = [threading.Thread(target=virtual_user, args=(i,), daemon=True) for i in range(vus)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall_s = time.perf_counter() - started
    return {"latencies": latencies, "failures": failures, "wall_s": wall_s}


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    names = [s["name"] for s in config["scenarios"]]

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenarios", nargs="+", default=names, choices=names)
    parser.add_argument("--duration", type=float, help="Override duration (seconds) for every scenario")
    parser.add_argument("--think-time", type=float, default=config["think_time_s"])
    parser.add_argument("--warmup", type=int, default=5, help="Untimed warm-up requests before measuring")
    parser.add_argument("--output", type=Path, default=RESULTS_DIR / "local_results.csv")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    try:
        health = httpx.get(f"{args.base_url.rstrip('/')}/health", timeout=5).json()
    except httpx.HTTPError as exc:
        print(f"API not reachable at {args.base_url}: {exc}", file=sys.stderr)
        return 1
    print(f"API healthy: {health.get('environment')} / {health.get('profiles_loaded')} profiles")

    with httpx.Client(timeout=10) as client:  # warm-up (not recorded)
        for _ in range(args.warmup):
            client.post(f"{args.base_url.rstrip('/')}/recommendations", json=PROFILES[0])

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    env_desc = f"{platform.system()} {platform.machine()} / Python {platform.python_version()} / uvicorn 1 worker"
    rows, raw = [], {}
    for scenario in config["scenarios"]:
        if scenario["name"] not in args.scenarios:
            continue
        duration = args.duration or scenario["duration_s"]
        print(f"Running {scenario['name']}: {scenario['vus']} VUs x {duration}s (think {args.think_time}s)...")
        result = run_scenario(args.base_url, scenario["vus"], duration, args.think_time)
        stats = summarise(result["latencies"])
        n = len(result["latencies"])
        row = {
            "measurement_label": "actual_local",
            "run_id": run_id,
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "environment": env_desc,
            "tool": "python-httpx (run_local_benchmark.py)",
            "target": args.base_url,
            "endpoint": "POST /recommendations",
            "scenario": scenario["name"],
            "vus": scenario["vus"],
            "duration_s": duration,
            "think_time_s": args.think_time,
            "requests": n,
            "failed_requests": result["failures"],
            "error_rate": (result["failures"] / n) if n else float("nan"),
            "throughput_rps": n / result["wall_s"] if result["wall_s"] else float("nan"),
            **stats,
            "notes": args.notes or "Client-side latency on localhost; not representative of AWS network latency.",
        }
        rows.append(row)
        raw[scenario["name"]] = [round(x, 3) for x in result["latencies"]]
        print(
            f"  requests={n} failed={result['failures']} avg={stats['avg_ms']:.2f}ms "
            f"p95={stats['p95_ms']:.2f}ms rps={row['throughput_rps']:.1f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    append_rows(args.output, rows)
    raw_dir = RESULTS_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"local_samples_{run_id}.json"
    raw_path.write_text(
        json.dumps({"measurement_label": "actual_local", "run_id": run_id, "samples_ms": raw}), encoding="utf-8"
    )
    json_path = args.output.with_suffix(".json")
    existing = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else {"runs": []}
    existing["runs"].append({"run_id": run_id, "measurement_label": "actual_local", "rows": rows})
    json_path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
    print(f"Appended {len(rows)} rows to {args.output}\nRaw samples: {raw_path}\nJSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
