# Experiments

> Owner: Member 3 · Method and definitions: [../docs/07_testing_and_experiments.md](../docs/07_testing_and_experiments.md)

| Path | Purpose |
|---|---|
| `k6/load_test.js`, `k6/scenarios.js` | k6 load test; scenarios `smoke`, `vu1`, `vu10`, `vu25`, `vu50` |
| `configs/scenarios.json` | Same scenarios for the Python benchmark |
| `configs/cost_inputs.json` | Cost-model inputs (prices intentionally `null`) |
| `run_local_benchmark.py` | Python closed-loop benchmark (fallback when k6 is not installed) |
| `run_local_experiments.sh` | Start the local API → run scenarios → analyse → chart |
| `run_aws_experiments.sh` | k6 against the deployed API → import → analyse → chart |
| `analysis/results_schema.py` | CSV columns, measurement labels, percentile maths |
| `analysis/collect_results.py` | Import k6 summary JSON files → CSV rows |
| `analysis/analyze_results.py` | Markdown summary table (refuses to mix labels) |
| `analysis/generate_charts.py` | PNG charts from `actual_*` rows only |
| `analysis/cost_model.py` | Cost per N requests |
| `cloudwatch/cold_start_queries.md` | Logs Insights queries for cold starts and billed duration |
| `results/` | CSV/JSON results and templates; see [results/README.md](results/README.md) |
| `charts/` | Generated charts |

## Quick commands (from the repository root, virtualenv active)

```bash
DURATION=30 bash experiments/run_local_experiments.sh                      # local, all scenarios
k6 run -e BASE_URL=http://localhost:8000 -e SCENARIO=smoke experiments/k6/load_test.js
API_URL=https://<id>.execute-api.<region>.amazonaws.com bash experiments/run_aws_experiments.sh
python experiments/analysis/cost_model.py --duration-ms <measured_billed_ms>
```

## Status

| Experiment | Status |
|---|---|
| Local latency and concurrency (1/10/25/50 VUs) | ✅ Actual local measurement, 2026-11-13 ([results/local_summary.md](results/local_summary.md)) |
| AWS latency and concurrency | ⏳ Pending cloud measurement |
| AWS cold starts | ⏳ Pending cloud measurement |
| Cost per 1,000 requests | ⏳ Needs AWS billed duration + current prices |
