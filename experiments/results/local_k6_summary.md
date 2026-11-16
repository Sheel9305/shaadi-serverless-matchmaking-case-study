**Measurement type: Actual local measurement** (`actual_local`)

Tool: k6 · Endpoint: recommendations · Environment: local Darwin arm64, uvicorn 1 worker, Python 3.14, k6 v2.4.0
Run(s): k6-20261116T105354Z

| Scenario | VUs | Requests | Error rate | Req/s | Avg ms | Min ms | Median ms | p90 ms | p95 ms | Max ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vu1 | 1 | 30 | 0.00% | 0.99 | 4.62 | 1.87 | 4.72 | 5.13 | 5.17 | 5.51 |
| vu10 | 10 | 300 | 0.00% | 9.84 | 16.14 | 9.93 | 16.12 | 18.50 | 19.31 | 25.73 |
| vu25 | 25 | 750 | 0.00% | 24.27 | 29.07 | 2.21 | 29.81 | 32.96 | 34.42 | 41.63 |
| vu50 | 50 | 1468 | 0.00% | 47.35 | 31.42 | 1.85 | 35.92 | 46.09 | 48.85 | 53.52 |
