# 5. Exercise plan

## 5.1 Course exercise requirement

*"Build a serverless function with an API trigger. Study cold starts and the cost per 1,000 requests."*

| Requirement | How we meet it | Evidence |
|---|---|---|
| Serverless function | AWS Lambda `shaadi-recommendation-api-<stage>` | `infrastructure/template.yaml`, Lambda console screenshot |
| API trigger | API Gateway HTTP API: `GET /health`, `POST /recommendations` | Stack outputs, curl output |
| Cold starts | `first_invocation_in_env` log field plus `Init Duration` in REPORT lines | `experiments/cloudwatch/cold_start_queries.md`, `cold_start_results.csv` |
| Cost per 1,000 requests | `cost_model.py` with measured billed duration and dated prices | `docs/08_cost_analysis.md` |

## 5.2 Five-week plan

| Week | Goal | Bhaumik (202301468) | Sheel (202301420) | Nakul (202301261) | Exit check |
|---|---|---|---|---|---|
| 1 | Research | Case-study research (all) | Case-study research | Case-study research | Week 1 summary |
| 2 | Foundations | Verify sources; draft 02 | Dataset, models, scoring | Frontend skeleton; k6 scenarios | Unit tests pass (110 passed) |
| 3 ✅ | Build | Diagrams; docs 03/04 | API, Lambda handler, logging | Frontend ↔ local API; result scripts | Local demo works |
| 4 ✅ | Cloud | Report draft & case study | SAM deploy; IAM; logs | AWS load tests; cold starts; cost | Real AWS numbers |
| 5 ⏳ | Integrate | Final report + slides | Fixes, reviews | Validation report | Submission + viva |

## 5.3 Experiment plan (summary; details in [07](07_testing_and_experiments.md))

| ID | Experiment | Variable | Measure | Where |
|---|---|---|---|---|
| E1 | Baseline latency | — (1 VU) | avg, min, median, max, p90, p95 | local ✅ + AWS ✅ |
| E2 | Concurrency | 1 / 10 / 25 / 50 VUs | latency percentiles, throughput, errors | local ✅ + AWS ✅ |
| E3 | Cold vs. warm | idle gap (e.g. 15+ min), new deploy | Init Duration, first vs. later duration | AWS ✅ |
| E4 | Memory size (optional) | 128 / 512 / 1024 MB | duration, cost per 1,000 | AWS only ⏳ not run (optional) |
| E5 | Cost per 1,000 requests | memory, duration | GB-s and USD | AWS + Price List API ✅ ($0.002510 per 1,000) |

## 5.4 Risks

| Risk | Mitigation |
|---|---|
| Unexpected AWS charges | Short tests, throttling, 7-day log retention, `sam delete` afterwards, AWS Budgets alert |
| `sam build` fails (Python version) | Install Python 3.12 or use `sam build --use-container` |
| Members blocked on each other | Frozen API contract; M3 works against the local API |
| Unverified case-study figures | Claims register with status labels |
