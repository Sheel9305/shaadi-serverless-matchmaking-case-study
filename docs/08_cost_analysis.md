# 8. Cost analysis: cost per 1,000 requests

> Owner: Member 3 · Script: [`experiments/analysis/cost_model.py`](../experiments/analysis/cost_model.py) · Inputs: [`experiments/configs/cost_inputs.json`](../experiments/configs/cost_inputs.json)
>
> **No AWS prices are written in this repository.** Prices change and differ by region. Look them up on the
> [AWS Pricing Calculator](https://calculator.aws/), the [Lambda pricing page](https://aws.amazon.com/lambda/pricing/) and the
> [API Gateway pricing page](https://aws.amazon.com/api-gateway/pricing/), and record the **date** you checked.

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

## 8.3 Inputs table (fill in after the AWS experiment)

| Input | Value | Source / status |
|---|---|---|
| Region | ap-south-1 (change if needed) | samconfig.toml |
| Memory | 512 MB | template parameter |
| Architecture | x86_64 | template |
| Avg billed duration (warm) | **⏳ pending AWS measurement** | Logs Insights query Q3 |
| Avg billed duration (incl. cold) | **⏳ pending AWS measurement** | Q3 |
| Cold-start share in test | **⏳ pending** | Q1 |
| Lambda price per 1M requests | **⏳ check calculator** | date: ____ |
| Lambda price per GB-s | **⏳ check calculator** | date: ____ |
| HTTP API price per 1M requests | **⏳ check calculator** | date: ____ |
| CloudWatch Logs ingestion per GB | **⏳ check calculator** | date: ____ |
| Data transfer out per GB | **⏳ check calculator** | date: ____ |

## 8.4 Running the model

```bash
python experiments/analysis/cost_model.py                          # shows usage; prices marked PRICE REQUIRED
python experiments/analysis/cost_model.py --duration-ms <measured> # after the AWS run
```

Current output (no prices, no AWS duration yet):

```
Cost model for 1,000 requests  (region: ap-south-1, memory: 512 MB, arch: x86_64)
Prices checked on: NOT YET CHECKED
  Average billed duration : PENDING AWS MEASUREMENT ms
  Lambda GB-seconds       : needs avg billed duration
  Lambda requests         : 1,000
  API Gateway requests    : 1,000
  Log data ingested       : 0.8583 MB
  Data transferred out    : 2.9297 MB
  ...
  TOTAL (before free tier): incomplete - fill all prices
```

### Worked example of the arithmetic (*illustrative*; numbers invented for teaching, **not** a result)

If the billed duration were 10 ms at 512 MB: `GB-s = 1000 × 0.010 × 0.5 = 5 GB-s` per 1,000 requests. Multiply by the current per-GB-s price, then add the per-request charges.

## 8.5 Discussion points for the report

- **Pay-per-use vs. always-on:** at low or bursty traffic Lambda costs almost nothing when idle. An always-on EC2 instance costs the same every hour. Compare against the hourly price of a small instance to find the break-even request rate (calculate it; don't guess).
- **Memory trade-off:** more memory costs more per ms but gives more CPU, so duration can drop. Optional experiment E4.
- **arm64 (Graviton):** usually a lower GB-s price. Changing `Architectures` is a one-line template change. Check the pricing page.
- **Free Tier:** may make a student test effectively free. Report the cost **before** Free Tier, and note it separately.
- **Hidden costs avoided:** no NAT gateway, no database, short log retention (7 days).
