**Measurement type: Actual local measurement** (`actual_local`)

Tool: python-httpx (run_local_benchmark.py) · Endpoint: POST /recommendations · Environment: Darwin arm64 / Python 3.14.3 / uvicorn 1 worker
Run(s): 20261113T161410Z-494296

| Scenario | VUs | Requests | Error rate | Req/s | Avg ms | Min ms | Median ms | p90 ms | p95 ms | Max ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vu1 | 1 | 30 | 0.00% | 0.99 | 5.43 | 1.18 | 5.91 | 6.54 | 6.66 | 6.75 |
| vu10 | 10 | 300 | 0.00% | 9.85 | 10.68 | 2.48 | 10.53 | 16.48 | 18.37 | 20.85 |
| vu25 | 25 | 750 | 0.00% | 24.35 | 15.63 | 1.47 | 16.94 | 22.91 | 25.37 | 42.82 |
| vu50 | 50 | 1500 | 0.00% | 48.43 | 20.89 | 1.62 | 20.33 | 35.19 | 37.16 | 45.72 |
