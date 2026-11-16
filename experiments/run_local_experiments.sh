#!/usr/bin/env bash
# Start the API locally, run the concurrency scenarios, then analyse + chart.
# Uses k6 if it is installed; otherwise falls back to the Python benchmark.
#
# Usage (from the repository root, with the virtualenv activated):
#   bash experiments/run_local_experiments.sh            # 30 s per scenario
#   DURATION=10 bash experiments/run_local_experiments.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${PORT:-8000}"
BASE_URL="http://127.0.0.1:${PORT}"
DURATION="${DURATION:-30}"
PY="${PYTHON:-python}"

echo "Starting API on ${BASE_URL} (1 uvicorn worker, access log off)..."
"$PY" -m uvicorn app:app --app-dir backend/src --port "$PORT" --log-level warning --no-access-log >/dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then break; fi
  sleep 0.5
done
curl -fsS "${BASE_URL}/health" >/dev/null || { echo "API did not start"; exit 1; }

if command -v k6 >/dev/null 2>&1; then
  for s in vu1 vu10 vu25 vu50; do
    k6 run -e BASE_URL="$BASE_URL" -e SCENARIO="$s" -e LABEL=local -e DURATION="${DURATION}s" experiments/k6/load_test.js
  done
  "$PY" experiments/analysis/collect_results.py --environment "local $(uname -sm), uvicorn 1 worker"
else
  echo "k6 not found - using the Python benchmark (experiments/run_local_benchmark.py)."
  "$PY" experiments/run_local_benchmark.py --base-url "$BASE_URL" --duration "$DURATION"
fi

"$PY" experiments/analysis/analyze_results.py --write experiments/results/local_summary.md
"$PY" experiments/analysis/generate_charts.py --prefix local
