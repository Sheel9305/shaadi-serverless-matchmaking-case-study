"""Structured (JSON) logging.

Each log line is a single JSON object, which makes it easy to search and
aggregate in Amazon CloudWatch Logs Insights, for example::

    fields @timestamp, event, route, status_code, duration_ms, first_invocation_in_env
    | filter event = "lambda_invocation"
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

SERVICE_NAME = os.getenv("SERVICE_NAME", "shaadi-recommendation-api")

logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
if not logging.getLogger().handlers and not logger.handlers:
    # Running locally (uvicorn/pytest). On Lambda the runtime installs a root handler.
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False


def log_event(event: str, level: int = logging.INFO, **fields: Any) -> dict[str, Any]:
    """Emit one structured log record and return it (handy for tests)."""
    record = {
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "level": logging.getLevelName(level),
        "service": SERVICE_NAME,
        "event": event,
        **fields,
    }
    logger.log(level, json.dumps(record, default=str))
    return record
