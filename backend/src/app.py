"""FastAPI application: GET /health and POST /recommendations.

Run locally (from the repository root):
    uvicorn app:app --app-dir backend/src --reload --port 8000

On AWS the same ``app`` object is wrapped by Mangum in ``lambda_handler.py``.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from logging_utils import log_event
from models import RecommendationRequest, RecommendationResponse
from recommendation_service import WEIGHTS, recommend
from repository import RepositoryError, get_repository
from validation import classify_errors, format_errors

APP_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("APP_ENV", "local")

app = FastAPI(
    title="Shaadi.com-inspired Matchmaking Recommendation API (IT457 student prototype)",
    description=(
        "Academic prototype. Uses SYNTHETIC profiles only and a transparent rules-based score. "
        "Not affiliated with Shaadi.com."
    ),
    version=APP_VERSION,
)

_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or "unknown"


def _error_response(request: Request, status: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"status": "error", "error": {"code": code, "message": message}, "request_id": _request_id(request)}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a request ID and measure server-side processing time."""
    aws_context = request.scope.get("aws.context")  # set by Mangum on Lambda
    request.state.request_id = (
        getattr(aws_context, "aws_request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())
    )
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 3)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    log_event(
        "http_request",
        request_id=request.state.request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = list(exc.errors())
    status, code, message = classify_errors(errors)
    details = format_errors(errors) if status == 422 else None
    log_event("validation_failed", logging.WARNING, request_id=_request_id(request), code=code, details=details)
    return _error_response(request, status, code, message, details)


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
    return _error_response(request, exc.status_code, codes.get(exc.status_code, "HTTP_ERROR"), str(exc.detail))


@app.exception_handler(RepositoryError)
async def handle_repository_error(request: Request, exc: RepositoryError):
    log_event("repository_error", logging.ERROR, request_id=_request_id(request), error=str(exc))
    return _error_response(request, 503, "DATA_UNAVAILABLE", "Candidate data is temporarily unavailable.")


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    log_event("unhandled_error", logging.ERROR, request_id=_request_id(request), error_type=type(exc).__name__)
    return _error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred.")


@app.get("/health")
def health(request: Request) -> dict:
    profiles = get_repository().list_candidates()
    return {
        "status": "healthy",
        "service": "shaadi-recommendation-api",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "profiles_loaded": len(profiles),
        "scoring_weights": WEIGHTS,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "request_id": _request_id(request),
    }


@app.post("/recommendations", response_model=RecommendationResponse, response_model_exclude_none=True)
def recommendations(payload: RecommendationRequest, request: Request) -> RecommendationResponse:
    start = time.perf_counter()
    result = recommend(payload, get_repository().list_candidates())
    log_event(
        "recommendations_generated",
        request_id=_request_id(request),
        user_id=payload.user_id,
        total_candidates=result.total_candidates,
        candidates_after_filters=result.candidates_after_filters,
        returned=len(result.recommendations),
        top_score=result.recommendations[0].compatibility_score if result.recommendations else None,
        scoring_ms=round((time.perf_counter() - start) * 1000, 3),
    )
    return RecommendationResponse(
        user_id=payload.user_id,
        total_candidates=result.total_candidates,
        candidates_after_filters=result.candidates_after_filters,
        recommendations=result.recommendations,
        message=result.message,
        request_id=_request_id(request),
    )
