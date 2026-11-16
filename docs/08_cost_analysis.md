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
| Avg billed duration (warm) | **⏳ pending CloudWatch** | Logs Insights query Q3 |
| Avg billed duration (incl. cold) | **⏳ pending CloudWatch** | Q3 |
| Cold-start share in test | **⏳ pending CloudWatch** | Q1/Q2 |
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
python experiments/analysis/cost_model.py                          # prices filled; billed duration pending
python experiments/analysis/cost_model.py --duration-ms <measured> # after the CloudWatch query
```

**Current output** (actual prices, billed duration still pending):

```
Cost model for 1,000 requests  (region: ap-south-1, memory: 512 MB, arch: x86_64)
Prices checked on: 2026-11-16
  Average billed duration : PENDING AWS MEASUREMENT ms
  Lambda GB-seconds       : needs avg billed duration
  Lambda requests         : 1,000
  API Gateway requests    : 1,000
  Log data ingested       : 0.8583 MB
  Data transferred out    : 2.0508 MB
Cost lines (USD):
  Lambda compute             : NEEDS BILLED DURATION
  Lambda requests            : $0.000200
  API Gateway (HTTP API)     : $0.001050
  CloudWatch Logs ingestion  : $0.000562
  Data transfer out          : $0.000219
  TOTAL (before free tier)   : incomplete - see lines above
```

**What we can already say from the known lines:** before the compute line is added, 1,000 requests cost **$0.002031** (about 0.2 US cents). **API Gateway is about half of that** ($0.00105). Compute depends on billed duration. The handler's own work takes about 2.5 ms, so billed duration is likely to be a few milliseconds, which would keep compute far below the API Gateway charge. **This is an expectation until CloudWatch confirms it.**

### Sensitivity of the total to billed duration (*illustrative*: the durations are assumed, the prices are real)

| Assumed billed duration | GB-s per 1,000 | Lambda compute | Total per 1,000 (before free tier) |
|---:|---:|---:|---:|
| 3 ms | 1.5 | $0.000025 | $0.002055 |
| 10 ms | 5 | $0.000083 | $0.002114 |
| 50 ms | 25 | $0.000417 | $0.002447 |

Data transfer uses the **measured** response size (2.1 KB). The log line uses an **assumed** 900 B per request; replace it with the CloudWatch `IncomingBytes` figure. Replace this table with the single measured value once Q3 has been run.

### Worked example of the arithmetic (*illustrative*; numbers invented for teaching, **not** a result)

If the billed duration were 10 ms at 512 MB: `GB-s = 1000 × 0.010 × 0.5 = 5 GB-s` per 1,000 requests. Multiply by the current per-GB-s price, then add the per-request charges.

## 8.5 Discussion points for the report

- **Pay-per-use vs. always-on:** at low or bursty traffic Lambda costs almost nothing when idle. An always-on EC2 instance costs the same every hour. Compare against the hourly price of a small instance to find the break-even request rate (calculate it; don't guess).
- **Memory trade-off:** more memory costs more per ms but gives more CPU, so duration can drop. Optional experiment E4.
- **arm64 (Graviton):** usually a lower GB-s price. Changing `Architectures` is a one-line template change. Check the pricing page.
- **Free Tier:** may make a student test effectively free. Report the cost **before** Free Tier, and note it separately.
- **Hidden costs avoided:** no NAT gateway, no database, short log retention (7 days).
