# Validation summary

> **Date:** 2026-11-13 · **Machine:** macOS (Darwin arm64), Python 3.14.3, Node.js 24.13.1
> **Tool versions:** fastapi 0.162.6, pydantic 2.14.3, mangum 0.22.0, pytest 9.2.0, pytest-cov 7.1.0, ruff 0.17.5, uvicorn 0.54.0, httpx 0.28.1; AWS SAM CLI 1.172.1 and cfn-lint 1.58.0 (in a separate throwaway virtualenv)
> Everything below was **actually executed**. Anything not executed is listed as such. Owner: Member 3 (update after every integration).

## 1. Results at a glance

| Check | Command | Result |
|---|---|---|
| Unit, API, handler and edge-case tests | `python -m pytest --cov` | ✅ **110 passed, 0 failed**, 99% line coverage (347 statements, 2 missed) |
| Python compile (22 files) | `scripts/validate_project.py` | ✅ |
| Import validation (7 backend modules) | `scripts/validate_project.py` | ✅ |
| JSON validation (8 files; dataset flagged synthetic) | `scripts/validate_project.py` | ✅ |
| YAML/TOML validation + SAM handler/route/CodeUri consistency | `scripts/validate_project.py` | ✅ |
| Mermaid sources (8) | `scripts/validate_project.py` | ✅ |
| Markdown relative links (107) | `scripts/validate_project.py` | ✅ |
| Secret / credential scan (85 files) | `scripts/validate_project.py` | ✅ none found |
| Validator negative test (injected a broken link + fake AWS key into a copy) | `validate_project.py` on the copy | ✅ both detected |
| Lint / static analysis | `ruff check .` | ✅ all checks passed (after fixes; see §3) |
| Python 3.11 compatibility (syntax) | `python3.11 -m py_compile backend/src/*.py` | ✅ |
| Frontend JS syntax | `node --check frontend/*.js` | ✅ |
| k6 script syntax (ES-module parse only; k6 APIs not executed) | `node --check --input-type=module` | ✅ |
| HTML structure (tag balance, duplicate IDs, IDs used by script.js, meta tags) | Python `html.parser` check | ✅ no errors |
| SAM template | `sam validate` and `sam validate --lint` | ✅ "valid SAM Template" |
| CloudFormation lint | `cfn-lint infrastructure/template.yaml` | ✅ no findings |
| Lambda dependency packaging | `pip install --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all: -r backend/src/requirements.txt` | ✅ resolves; about 16 MB unzipped |
| `sam build` | `sam build` | ❌ **not completed**: needs `python3.12` on PATH (machine has 3.11 and 3.14) and no Docker for `--use-container` |
| Browser end-to-end (headless Chrome via Puppeteer, frontend on :5500 → API on :8000) | scratch Puppeteer script | ✅ health indicator, U001 results (U161=97, U162=80, U133=62, U117=60, U144=59), strict-city filter (Pune only), no-match message, client-side age error, server 422 shown in UI, no horizontal scroll at 375 px; only console error = the deliberate 422 |
| Local load experiment (1/10/25/50 VUs × 30 s) | `bash experiments/run_local_experiments.sh` | ✅ 2,580 requests, 0 errors (`actual_local`, see §4) |
| Diagram rendering (8 × SVG + PNG) | `bash scripts/generate_diagrams.sh` (mermaid-cli 11.4.2 with system Chrome) | ✅ 16 files, all non-empty (15–270 KB) |

## 2. Exact commands executed

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python backend/scripts/generate_profiles.py
PYTHON=.venv/bin/python bash scripts/run_tests.sh          # validation + ruff + node --check + pytest/coverage
python3.11 -m py_compile backend/src/*.py
cd infrastructure && sam validate && sam validate --lint && cfn-lint template.yaml
SAM_CLI_TELEMETRY=0 sam build                              # failed: python3.12 not found (expected on this machine)
pip install --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all: \
    -r backend/src/requirements.txt -t <scratch dir>
PYTHON=.venv/bin/python DURATION=30 bash experiments/run_local_experiments.sh
python experiments/analysis/cost_model.py
MMDC=<mmdc> PUPPETEER_CONFIG=<chrome config> bash scripts/generate_diagrams.sh
```

Note: the first `sam validate` call sent SAM CLI's default anonymous usage telemetry. Later SAM commands set `SAM_CLI_TELEMETRY=0`. The deployment guide explains how to turn telemetry off.

## 3. Failures found and fixed (then re-run)

| # | Problem | Fix | Re-run |
|---|---|---|---|
| 1 | `test_first_invocation_flag_and_structured_log` failed: caplog captured each record twice through logger propagation | Spy on `log_event` instead of caplog | Handler tests 8/8, then full suite 110/110 ✅ |
| 2 | ruff: `UP017` (`datetime.UTC`), `UP035`, `UP037` in 4 files | `ruff check --fix` + `ruff format` | 110/110 ✅, ruff clean |
| 3 | ruff `E501` in `validate_project.py` | `ruff format` | ✅ |
| 4 | `generate_diagrams.sh` crashed on macOS bash 3.2 (`extra[@]: unbound variable`) | Safe empty-array expansion | Rendered 16/16 ✅ |
| 5 | `npx @mermaid-js/mermaid-cli` hung downloading Chromium | Script now accepts `MMDC` and `PUPPETEER_CONFIG` to reuse an installed Chrome | ✅ |
| 6 | Doc 07 per-file test counts were wrong (23→24, 10→9) | Corrected from `pytest --collect-only` | ✅ |
| 7 | Dark mode: low-contrast white text on the pink button | `--on-accent` colour token | Browser e2e re-run ✅ |
| 8 | Browser requested a missing `/favicon.ico` (404 in console) | Inline empty favicon | Browser e2e re-run ✅ |
| 9 | Logs Insights query Q4 used an invalid `sum()` on a string | Rewritten as `stats count(*) by first_inv` | Not executed (AWS only) |
| 10 | (2026-11-16) k6 v2.4.0: `handleSummary` crashed (`Cannot read property 'vus' of undefined`), so no summary JSON was saved | Read VUs/duration from `SCENARIOS`/`__ENV` instead of `options` | k6 smoke run saves JSON ✅ |
| 11 | (2026-11-16) `collect_results.py` gave every k6 file its own `run_id`, so "latest run" charts showed only the 50-VU scenario | One shared `run_id` per import batch | 4-scenario k6 import + charts ✅ |

## 4. Local experiment (Actual local measurement)

Run `20261113T161410Z-494296`. Python httpx closed-loop client (k6 not installed), uvicorn with 1 worker, 1 s think time. Files: `experiments/results/local_results.csv`, `local_results.json`, `local_summary.md`, `raw/local_samples_*.json`, `experiments/charts/local_*.png`.

| VUs | Requests | Errors | Req/s | Avg ms | Median ms | p90 ms | p95 ms | Max ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 30 | 0% | 0.99 | 5.43 | 5.91 | 6.54 | 6.66 | 6.75 |
| 10 | 300 | 0% | 9.85 | 10.68 | 10.53 | 16.48 | 18.37 | 20.85 |
| 25 | 750 | 0% | 24.35 | 15.63 | 16.94 | 22.91 | 25.37 | 42.82 |
| 50 | 1500 | 0% | 48.43 | 20.89 | 20.33 | 35.19 | 37.16 | 45.72 |

## 4b. Local experiment with k6 (Actual local measurement, 2026-11-16)

Run `k6-20261116T105354Z`, k6 v2.4.0 (installed with `brew install k6`), same API code and scenarios, uvicorn with 1 worker. Commands:

```bash
k6 run -e BASE_URL=http://127.0.0.1:8000 -e SCENARIO=<vu1|vu10|vu25|vu50> -e LABEL=local -e DURATION=30s experiments/k6/load_test.js
python experiments/analysis/collect_results.py --environment "local Darwin arm64, uvicorn 1 worker, Python 3.14, k6 v2.4.0"
python experiments/analysis/analyze_results.py --write experiments/results/local_k6_summary.md
python experiments/analysis/generate_charts.py --prefix local_k6
```

| VUs | Requests | Errors | Req/s | Avg ms | Median ms | p90 ms | p95 ms | Max ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 30 | 0% | 0.99 | 4.62 | 4.72 | 5.13 | 5.17 | 5.51 |
| 10 | 300 | 0% | 9.84 | 16.14 | 16.12 | 18.50 | 19.31 | 25.73 |
| 25 | 750 | 0% | 24.27 | 29.07 | 29.81 | 32.96 | 34.42 | 41.63 |
| 50 | 1468 | 0% | 47.35 | 31.42 | 35.92 | 46.09 | 48.85 | 53.52 |

All k6 checks passed: status 200 and a recommendations array in every response.

## 5. Not tested here (with reason) — the team must run these

| Item | Why not | Who / how |
|---|---|---|
| `sam build` | No Python 3.12 and no Docker on this machine | M2: install Python 3.12 or Docker, then `sam build` |
| `sam local invoke` / `start-api` | Needs Docker | M2 |
| **AWS deployment** | No AWS credentials used (by design) | M2: `sam deploy --guided` |
| **AWS latency, concurrency** | Requires deployment | M3: `run_aws_experiments.sh` |
| **Lambda cold starts** (Init Duration, count) | Requires deployment | M3: `experiments/cloudwatch/cold_start_queries.md` |
| **Billed duration → cost per 1,000 requests** | Requires deployment + current prices | M3: `cost_model.py --duration-ms …` |
| k6 execution against AWS | Requires deployment (local k6 run done 2026-11-16, see §4b) | M3: `run_aws_experiments.sh` |
| CORS from a hosted frontend to API Gateway | Requires deployment | M3 |
| W3C HTML validator / html-validate | Not installed; Python structural check used instead | Optional: `npx html-validate frontend/index.html` |
| Windows `run_tests.ps1` | macOS machine | Any member on Windows |

## 6. Checks that require AWS deployment

Deployed `/health` returns 200 · deployed `/recommendations` returns the same top result as locally (U161 = 97) · CORS preflight from the frontend origin · CloudWatch log group receives `lambda_init` and `lambda_invocation` JSON lines · REPORT lines show `Init Duration` on cold starts · throttling returns 429 above 50 rps (optional; don't overload) · `sam delete` removes all resources.
