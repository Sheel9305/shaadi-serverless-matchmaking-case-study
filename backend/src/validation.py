"""Request validation helpers.

Field-level rules (types, ranges, duplicates, ...) are declared on the Pydantic
models in ``models.py``. This module turns Pydantic/FastAPI validation errors
into the API's consistent error format and decides the HTTP status code:

* **400 Bad Request** - the body as a whole is unusable: missing, not valid
  JSON, or not a JSON object.
* **422 Unprocessable Entity** - the body is a JSON object but one or more
  fields break a rule (missing field, wrong type, age out of range, ...).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from models import RecommendationRequest

BODY_LEVEL_ERROR_TYPES = {"json_invalid", "missing", "model_attributes_type", "dict_type", "model_type"}


def _field_path(loc: Iterable[Any]) -> str:
    parts = [str(p) for p in loc if p != "body"]
    return ".".join(parts) if parts else "body"


def _clean_message(error: dict[str, Any]) -> str:
    message = str(error.get("msg", "Invalid value"))
    # Pydantic prefixes custom validator errors with "Value error, ".
    return message.removeprefix("Value error, ")


def format_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert Pydantic error dicts into ``[{"field": ..., "message": ...}]``."""
    return [
        {"field": _field_path(e.get("loc", ())), "message": _clean_message(e), "type": str(e.get("type", ""))}
        for e in errors
    ]


def classify_errors(errors: list[dict[str, Any]]) -> tuple[int, str, str]:
    """Return ``(http_status, error_code, human_message)`` for a list of errors."""
    for error in errors:
        loc = tuple(error.get("loc", ()))
        if error.get("type") == "json_invalid":
            return 400, "INVALID_JSON", "Request body is not valid JSON."
        if loc == ("body",) and error.get("type") in BODY_LEVEL_ERROR_TYPES:
            if error.get("type") == "missing":
                return 400, "MISSING_BODY", "Request body is required."
            return 400, "INVALID_BODY", "Request body must be a JSON object."
    return 422, "VALIDATION_ERROR", "One or more fields are invalid."


def validate_request_payload(payload: Any) -> RecommendationRequest:
    """Validate a raw (already JSON-decoded) payload outside FastAPI.

    Useful for unit tests and for any future non-HTTP trigger (e.g. an SQS or
    EventBridge event) that needs the same rules. Raises ``ValidationError``.
    """
    return RecommendationRequest.model_validate(payload)


__all__ = ["ValidationError", "classify_errors", "format_errors", "validate_request_payload"]
