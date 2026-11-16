"""Transparent cost model: estimated cost of N (default 1,000) API requests.

No AWS prices are hard-coded. Fill them into experiments/configs/cost_inputs.json
from the AWS Pricing Calculator for your region and date. Until then the script
prints the usage quantities and the formula, with "PRICE REQUIRED" in place of
dollar amounts.

Formulae (per run of N requests):

    GB-seconds       = N x (billed_duration_ms / 1000) x (memory_mb / 1024)
    Lambda compute   = GB-seconds x price_per_GB_second
    Lambda requests  = N / 1,000,000 x price_per_1M_requests
    API Gateway      = N / 1,000,000 x HTTP_API_price_per_1M_requests
    CloudWatch Logs  = N x log_bytes / 1024^3 x price_per_GB_ingested
    Data transfer    = N x response_kb / 1024^2 x price_per_GB_out
    Total            = sum of the above (before any free tier)

Usage:
    python experiments/analysis/cost_model.py
    python experiments/analysis/cost_model.py --duration-ms 12 --memory-mb 512 --requests 1000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "configs" / "cost_inputs.json"


def compute(inputs: dict) -> dict:
    n = inputs["requests"]
    mem_gb = inputs["lambda_memory_mb"] / 1024
    duration_ms = inputs.get("avg_billed_duration_ms")
    prices = inputs["prices_usd"]

    usage = {
        "requests": n,
        "gb_seconds": None if duration_ms is None else n * (duration_ms / 1000) * mem_gb,
        "log_gb": n * inputs["log_bytes_per_request"] / 1024**3,
        "transfer_gb": n * inputs["avg_response_size_kb"] / 1024**2,
    }

    def cost(quantity, price):
        return None if quantity is None or price is None else quantity * price

    lines = {
        "Lambda compute": cost(usage["gb_seconds"], prices.get("lambda_per_gb_second")),
        "Lambda requests": cost(n / 1_000_000, prices.get("lambda_per_1m_requests")),
        "API Gateway (HTTP API)": cost(n / 1_000_000, prices.get("api_gateway_http_per_1m_requests")),
        "CloudWatch Logs ingestion": cost(usage["log_gb"], prices.get("cloudwatch_logs_ingest_per_gb")),
        "Data transfer out": cost(usage["transfer_gb"], prices.get("data_transfer_out_per_gb")),
    }
    total = None if any(v is None for v in lines.values()) else sum(lines.values())
    return {"usage": usage, "lines": lines, "total": total}


def render(inputs: dict, result: dict) -> str:
    u = result["usage"]
    out = [
        f"Cost model for {u['requests']:,} requests  (region: {inputs['region']}, "
        f"memory: {inputs['lambda_memory_mb']} MB, arch: {inputs['lambda_architecture']})",
        f"Prices checked on: {inputs.get('pricing_checked_on') or 'NOT YET CHECKED'}",
        "",
        "Usage quantities:",
        f"  Average billed duration : {inputs.get('avg_billed_duration_ms') or 'PENDING AWS MEASUREMENT'} ms",
        f"  Lambda GB-seconds       : {u['gb_seconds']:.4f}"
        if u["gb_seconds"] is not None
        else "  Lambda GB-seconds       : needs avg billed duration",
        f"  Lambda requests         : {u['requests']:,}",
        f"  API Gateway requests    : {u['requests']:,}",
        f"  Log data ingested       : {u['log_gb'] * 1024:.4f} MB",
        f"  Data transferred out    : {u['transfer_gb'] * 1024:.4f} MB",
        "",
        "Cost lines (USD):",
    ]
    for name, value in result["lines"].items():
        out.append(f"  {name:<27}: {'PRICE REQUIRED' if value is None else f'${value:.6f}'}")
    out.append(
        f"  {'TOTAL (before free tier)':<27}: "
        + ("incomplete - fill all prices" if result["total"] is None else f"${result['total']:.6f}")
    )
    out.append("")
    out.append("Free tier: check current AWS Free Tier terms for your account; not applied in this estimate.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--requests", type=int)
    parser.add_argument("--memory-mb", type=int)
    parser.add_argument("--duration-ms", type=float, help="Average *billed* duration from CloudWatch REPORT lines")
    args = parser.parse_args()

    inputs = json.loads(args.config.read_text(encoding="utf-8"))
    if args.requests:
        inputs["requests"] = args.requests
    if args.memory_mb:
        inputs["lambda_memory_mb"] = args.memory_mb
    if args.duration_ms is not None:
        inputs["avg_billed_duration_ms"] = args.duration_ms
    print(render(inputs, compute(inputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
