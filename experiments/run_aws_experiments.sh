#!/usr/bin/env bash
# Run the k6 scenarios against the DEPLOYED AWS API (requires k6).
#
#   API_URL=https://<api-id>.execute-api.<region>.amazonaws.com bash experiments/run_aws_experiments.sh
#
# Afterwards, collect cold-start and billed-duration data from CloudWatch
# (see experiments/cloudwatch/cold_start_queries.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "${API_URL:?Set API_URL to the ApiBaseUrl stack output}"
PY="${PYTHON:-python}"
DURATION="${DURATION:-30}"
ENV_DESC="${ENV_DESC:-AWS $(aws configure get region 2>/dev/null || echo region?) 512MB x86_64}"

command -v k6 >/dev/null || { echo "k6 is required: https://grafana.com/docs/k6/latest/set-up/install-k6/"; exit 1; }
curl -fsS "${API_URL}/health" || { echo "Health check failed"; exit 1; }

for s in vu1 vu10 vu25 vu50; do
  k6 run -e BASE_URL="$API_URL" -e SCENARIO="$s" -e LABEL=aws -e DURATION="${DURATION}s" experiments/k6/load_test.js
  sleep 5
done
"$PY" experiments/analysis/collect_results.py --environment "$ENV_DESC"
"$PY" experiments/analysis/analyze_results.py --input experiments/results/cloud_results.csv --write experiments/results/cloud_summary.md
"$PY" experiments/analysis/generate_charts.py --input experiments/results/cloud_results.csv --prefix aws
