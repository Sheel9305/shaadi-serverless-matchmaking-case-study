# Results

Every row carries exactly one `measurement_label`:

| Label | Meaning |
|---|---|
| `actual_local` | Measured by us on a laptop against the local API |
| `actual_aws` | Measured by us against the deployed AWS API |
| `pending_cloud` | Placeholder row; the AWS measurement has not been collected yet |
| `illustrative` | Teaching example; never a result |

| File | Contents | Status |
|---|---|---|
| `local_results.csv` | Latency/throughput per scenario (columns in `analysis/results_schema.py`) | ✅ `actual_local` runs `20261113T161410Z-494296` (Python client) and `k6-20261116T105354Z` (k6) |
| `local_k6_summary.md` | Markdown table for the k6 run | ✅ |
| `raw/k6_local_*.json` | Full k6 end-of-test summaries (JSON) for the k6 run | ✅ |
| `local_results.json` | The same rows as JSON, grouped by run | ✅ |
| `local_summary.md` | Markdown table from `analyze_results.py` | ✅ |
| `raw/local_samples_*.json` | Every individual latency sample (ms) | ✅ |
| `cloud_results_template.csv` | Same columns; one `pending_cloud` row per scenario | ⏳ template |
| `cold_start_template.csv` | Columns for cold vs. warm observations | ⏳ template |
| `cloud_results.csv` | AWS k6 runs | ✅ `actual_aws` run `k6-20261116T162319Z` |
| `cloud_summary.md` | Markdown table of the AWS run | ✅ |
| `cold_start_results.csv` | Cold vs warm on AWS: client latency + Lambda REPORT fields (matched on request_id) | ✅ |
| `raw/cloudwatch_*_20261116.csv` | CloudWatch Logs Insights exports: billed-duration stats, log bytes, REPORT lines of the cold probe | ✅ |
| `raw/cold_probe_aws_20261116.json` | Raw cold-start probe (11 requests) | ✅ |
| `raw/k6_aws_*.json` | k6 summaries of the AWS run | ✅ |

The full raw CloudWatch export (18k lines) is **not** committed because it contains client IP addresses. Only aggregates and the REPORT lines are kept.

Do not edit measured rows by hand. Re-run the experiment instead. Keep failed or odd runs and add a note rather than deleting them.
