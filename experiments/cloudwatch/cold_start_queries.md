# CloudWatch Logs Insights queries (AWS only)

Open **CloudWatch → Logs Insights**, select the log group `/aws/lambda/shaadi-recommendation-api-dev`, choose a time range that covers the experiment, and run the queries below.
Results from these queries are **actual AWS measurements**. Record them with the `actual_aws` label.

## Q1 — Cold starts from Lambda platform REPORT lines

```
filter @type = "REPORT"
| fields @timestamp, @requestId, @initDuration, @duration, @billedDuration, @maxMemoryUsed / 1000 / 1000 as maxMemMB
| sort @timestamp asc
```

`@initDuration` is present **only** for invocations that needed a new execution environment (cold start).

## Q2 — Cold vs. warm summary

```
filter @type = "REPORT"
| stats count(*) as invocations,
        count(@initDuration) as cold_starts,
        avg(@initDuration) as avg_init_ms,
        max(@initDuration) as max_init_ms,
        avg(@duration) as avg_duration_ms,
        pct(@duration, 95) as p95_duration_ms
```

## Q3 — Billed duration for the cost model

```
filter @type = "REPORT"
| stats avg(@billedDuration) as avg_billed_ms, pct(@billedDuration, 50) as p50_billed_ms,
        pct(@billedDuration, 95) as p95_billed_ms, count(*) as n
```

Use `avg_billed_ms` in `python experiments/analysis/cost_model.py --duration-ms <avg_billed_ms>`.

## Q4 — Our structured log: first invocation per environment

```
filter @message like /"event": "lambda_invocation"/
| parse @message '"first_invocation_in_env": *,' as first_inv
| parse @message '"module_init_ms": *,' as module_init_ms
| stats count(*) as invocations by first_inv
```

`first_inv = true` rows should match the `cold_starts` count from Q2. To list them with their module-init time:

```
filter @message like /"first_invocation_in_env": true/
| parse @message '"module_init_ms": *,' as module_init_ms
| fields @timestamp, @requestId, module_init_ms
```

(Our JSON field order is fixed, so `parse` works reliably.)

## Q5 — Errors and validation failures

```
filter @message like /"level": "(WARNING|ERROR)"/
| parse @message '"event": "*"' as evt
| stats count(*) by evt
```

## API Gateway access logs (`/aws/apigateway/shaadi-recommendation-api-dev`)

```
fields @timestamp, routeKey, status, integrationLatency, responseLatency
| stats avg(responseLatency) as avg_resp_ms, pct(responseLatency, 95) as p95_resp_ms,
        avg(integrationLatency) as avg_integration_ms by routeKey
```

`responseLatency − integrationLatency` ≈ time API Gateway itself adds.

## CLI alternative

```bash
aws logs start-query --log-group-name /aws/lambda/shaadi-recommendation-api-dev \
  --start-time $(date -d '-1 hour' +%s) --end-time $(date +%s) \
  --query-string 'filter @type = "REPORT" | stats count(*) as n, count(@initDuration) as cold'
aws logs get-query-results --query-id <id-from-previous-command>
```

(On macOS use `date -v-1H +%s` instead of `date -d '-1 hour' +%s`.)
