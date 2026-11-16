# 8. Cost analysis: cost per 1,000 requests

> Owner: Member 3 · Script: [`experiments/analysis/cost_model.py`](../experiments/analysis/cost_model.py) · Inputs: [`experiments/configs/cost_inputs.json`](../experiments/configs/cost_inputs.json)
>
> **Prices are dated, never hard-coded in code.** They live only in `cost_inputs.json`, together with the date they were checked
> and their source. The current values were taken on **2026-11-16** from the official **AWS Price List API** offer files for ap-south-1.
> Prices change, so re-check them on the [AWS Pricing Calculator](https://calculator.aws/), the [Lambda pricing page](https://aws.amazon.com/lambda/pricing/) and the
> [API Gateway pricing page](https://aws.amazon.com/api-gateway/pricing/) before the final report.

## 8.1 Billable items for one request

| # | Item | Unit | Driver |
|---|---|---|---|
| 1 | Lambda requests | per 1M requests | number of invocations |
| 2 | Lambda compute | per GB-second | billed duration × configured memory |
| 3 | API Gateway HTTP API | per 1M requests | number of API calls |
| 4 | CloudWatch Logs ingestion | per GB | bytes of logs written (we write about 3 JSON lines + platform lines per request) |
| 5 | Data transfer out | per GB | response size (about 3 KB for top 5) |
| — | Not charged in this design | — | no database, no NAT gateway, no provisioned concurrency |

## 8.2 Formula

```
GB_seconds        = N × (avg_billed_duration_ms / 1000) × (memory_MB / 1024)
Lambda_compute    = GB_seconds × P_gb_s
Lambda_requests   = (N / 1,000,000) × P_lambda_1M
API_Gateway       = (N / 1,000,000) × P_httpapi_1M
CloudWatch_Logs   = N × log_bytes / 1024³ × P_logs_GB
Data_transfer     = N × response_KB / 1024² × P_out_GB
Cost(N)           = sum of the above  (before Free Tier)
```

With N = 1,000 and 512 MB, the only measured input is **average billed duration**, which comes from the `REPORT` lines on AWS.

## 8.3 Inputs table

| Input | Value | Source / status |
|---|---|---|
| Region | ap-south-1 (Mumbai) | samconfig.toml (deployed stack) |
| Memory | 512 MB | template parameter |
| Architecture | x86_64 | template |
| Avg billed duration (all invocations, incl. cold) | **12.593 ms** (p50 5 ms, p95 14 ms, n = 2,398) | *Actual AWS*, CloudWatch REPORT lines, 2026-11-16 (`results/raw/cloudwatch_billed_duration_20261116.csv`) |
| Avg billed duration (warm only) | 6.74 ms (n = 1,420) | *Actual AWS*, raw REPORT sample 16:21:55–16:42 UTC |
| Billed duration of one cold start | 1,351–1,379 ms (includes about 1.1 s `Init Duration`) | *Actual AWS*, 2 cold starts observed |
| Log bytes per request | **1,500.6 B** (about 6 lines) | *Actual AWS*: 3,598,513 B / 2,398 invocations (`results/raw/cloudwatch_log_bytes_20261116.csv`) |
| Response size | 2.1 KB | *Actual AWS*: 1,919 B body + 234 B headers |
| Lambda price per 1M requests | **$0.20** | Price List API `AWSLambda`, usage type `APS3-Request` (published 2026-11-11), checked 2026-11-16 |
| Lambda price per GB-s (x86, Tier 1) | **$0.0000166667** | `APS3-Lambda-GB-Second` (same file) |
| HTTP API price per 1M requests (first 300M) | **$1.05** | `AmazonApiGateway`, `APS3-ApiGatewayHttpRequest` (published 2026-11-12) |
| CloudWatch Logs ingestion per GB (Standard) | **$0.67** | `AmazonCloudWatch`, `APS3-DataProcessing-Bytes` (published 2026-11-04) |
| Data transfer out per GB (first 10 TB after free 100 GB) | **$0.1093** | `AWSDataTransfer`, `APS3-DataTransfer-Out-Bytes` (published 2026-11-11) |
| *(for comparison)* Lambda GB-s, arm64 | $0.0000133334 | `APS3-Lambda-GB-Second-ARM`: 20% cheaper compute |
| Free tier (not applied) | 1M Lambda requests, 400,000 GB-s/month; 100 GB data out/month; 5 GB logs | same offer files |

Price List API URL pattern: `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<service>/current/ap-south-1/index.json`.

## 8.4 Running the model

```bash
python experiments/analysis/cost_model.py                    # uses the measured 12.593 ms from cost_inputs.json
python experiments/analysis/cost_model.py --duration-ms 6.74 # warm-only variant
```

**Result** (*actual AWS measurement* for duration, logs and response size; prices dated 2026-11-16):

```
Cost model for 1,000 requests  (region: ap-south-1, memory: 512 MB, arch: x86_64)
Prices checked on: 2026-11-16
  Average billed duration : 12.593 ms
  Lambda GB-seconds       : 6.2965
  Lambda requests         : 1,000
  API Gateway requests    : 1,000
  Log data ingested       : 1.4311 MB
  Data transferred out    : 2.0508 MB
Cost lines (USD):
  Lambda compute             : $0.000105
  Lambda requests            : $0.000200
  API Gateway (HTTP API)     : $0.001050
  CloudWatch Logs ingestion  : $0.000936
  Data transfer out          : $0.000219
  TOTAL (before free tier)   : $0.002510
```

### Cost per 1,000 requests: **$0.002510** (about 0.25 US cents, before Free Tier)

| Item | USD per 1,000 | Share |
|---|---:|---:|
| API Gateway (HTTP API) | 0.001050 | 41.8% |
| CloudWatch Logs ingestion | 0.000936 | 37.3% |
| Data transfer out | 0.000219 | 8.7% |
| Lambda requests | 0.000200 | 8.0% |
| Lambda compute | 0.000105 | 4.2% |
| **Total** | **0.002510** | 100% |

That works out to about **$2.51 per million requests**.

**Findings**
1. **Compute is the smallest line (4%).** The handler runs in about 5 ms, so a request costs almost nothing in GB-seconds, even at 512 MB.
2. **Logging costs about 9× as much as compute.** We write about 1.5 KB of logs per request: our 3 JSON lines plus START/END/REPORT. Halving the logs (for example, dropping the duplicate `http_request` line, or sampling at INFO level) would save more than removing compute entirely. Our first guess, 900 B, was 40% too low, which is why the measured value replaces it.
3. **Per-request charges dominate** (API Gateway + Lambda requests = 50%). They are fixed per call, so the main way to cut them is fewer calls (caching, batching).
4. **Cold starts double the compute line, but not the total.** Warm-only billing (6.74 ms) would give compute $0.000056 and a total of $0.002461. Cold starts therefore add about 2% to the total.
5. **Not included:** Free Tier (it would make this test free), CloudWatch storage beyond 7 days, and the API Gateway access-log group (about 190 B per request; it is a separate log group with the same ingestion price, about $0.00012 per 1,000).

## 8.5 Discussion points for the report

- **Pay-per-use vs. always-on:** at low or bursty traffic Lambda costs almost nothing when idle. An always-on EC2 instance costs the same every hour. Compare against the hourly price of a small instance to find the break-even request rate (calculate it; don't guess).
- **Memory trade-off:** more memory costs more per ms but gives more CPU, so duration can drop. Optional experiment E4.
- **arm64 (Graviton):** usually a lower GB-s price. Changing `Architectures` is a one-line template change. Check the pricing page.
- **Free Tier:** may make a student test effectively free. Report the cost **before** Free Tier, and note it separately.
- **Hidden costs avoided:** no NAT gateway, no database, short log retention (7 days).
