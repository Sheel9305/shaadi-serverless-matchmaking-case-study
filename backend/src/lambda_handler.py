"""AWS Lambda entry point (Handler: lambda_handler.handler).

API Gateway HTTP API (payload format 2.0) -> this handler -> Mangum -> FastAPI.

Cold-start instrumentation
--------------------------
Module-level code runs once per Lambda *execution environment* (the "Init"
phase). We record when that happened and flag the first invocation that the
environment serves. Combined with the ``Init Duration`` value that Lambda
prints in the ``REPORT`` log line of cold invocations, this lets the team
identify and count cold starts in CloudWatch Logs Insights.

Note: running this handler locally (pytest, ``sam local``) is NOT an AWS cold
start measurement - it only exercises the same code path.
"""

from __future__ import annotations

import os
import time

_INIT_STARTED = time.perf_counter()

from mangum import Mangum  # noqa: E402

from app import app  # noqa: E402
from logging_utils import log_event  # noqa: E402
from repository import get_repository  # noqa: E402

# Load the synthetic dataset during Init so warm invocations reuse it.
_PROFILE_COUNT = len(get_repository().list_candidates())
INIT_DURATION_MS = round((time.perf_counter() - _INIT_STARTED) * 1000, 3)

_mangum = Mangum(app, lifespan="off")
_state = {"invocations": 0}

log_event("lambda_init", module_init_ms=INIT_DURATION_MS, profiles_loaded=_PROFILE_COUNT)


def _route(event: dict) -> str:
    http = (event.get("requestContext") or {}).get("http") or {}
    method = http.get("method") or event.get("httpMethod") or "UNKNOWN"
    path = http.get("path") or event.get("rawPath") or event.get("path") or "UNKNOWN"
    return f"{method} {path}"


def handler(event: dict, context) -> dict:
    _state["invocations"] += 1
    first_invocation = _state["invocations"] == 1
    start = time.perf_counter()

    response = _mangum(event, context)

    log_event(
        "lambda_invocation",
        request_id=getattr(context, "aws_request_id", None),
        route=_route(event),
        status_code=response.get("statusCode"),
        duration_ms=round((time.perf_counter() - start) * 1000, 3),
        first_invocation_in_env=first_invocation,
        invocation_number_in_env=_state["invocations"],
        module_init_ms=INIT_DURATION_MS if first_invocation else None,
        memory_limit_mb=getattr(context, "memory_limit_in_mb", None),
        function_version=getattr(context, "function_version", None),
        region=os.getenv("AWS_REGION", "local"),
    )
    return response
