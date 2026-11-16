**Measurement type: Actual AWS measurement** (`actual_aws`)

Tool: k6 · Endpoint: recommendations · Environment: AWS ap-south-1, Lambda python3.12 512MB x86_64, HTTP API; client: k6 v2.4.0 on MacBook (Darwin arm64)
Run(s): k6-20261116T162319Z

| Scenario | VUs | Requests | Error rate | Req/s | Avg ms | Min ms | Median ms | p90 ms | p95 ms | Max ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vu1 | 1 | 26 | 0.00% | 0.85 | 75.44 | 63.99 | 73.25 | 90.13 | 92.33 | 110.87 |
| vu10 | 10 | 283 | 0.00% | 9.12 | 66.54 | 27.84 | 56.00 | 70.79 | 82.17 | 1466.40 |
| vu25 | 25 | 563 | 0.00% | 18.18 | 56.30 | 28.04 | 56.93 | 73.77 | 85.19 | 440.86 |
| vu50 | 50 | 1446 | 5.50% | 46.55 | 49.70 | 22.06 | 54.46 | 68.87 | 72.33 | 322.35 |
