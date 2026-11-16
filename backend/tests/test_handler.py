"""Tests for the AWS Lambda handler using sample API Gateway HTTP API (v2) events.

These run the real handler locally. They prove the Lambda integration works,
but they are NOT AWS cold-start measurements.
"""

from __future__ import annotations

import base64
import json
import logging
from types import SimpleNamespace

import pytest

import lambda_handler


class FakeContext(SimpleNamespace):
    def get_remaining_time_in_millis(self) -> int:
        return 10_000


def make_context(request_id: str = "test-request-id") -> FakeContext:
    return FakeContext(
        aws_request_id=request_id,
        function_name="shaadi-recommendation-api",
        function_version="$LATEST",
        memory_limit_in_mb=512,
        invoked_function_arn="arn:aws:lambda:ap-south-1:123456789012:function:test",
        log_group_name="/aws/lambda/test",
        log_stream_name="test-stream",
    )


@pytest.fixture(autouse=True)
def reset_invocation_counter():
    lambda_handler._state["invocations"] = 0
    yield


def test_health_event(load_event):
    response = lambda_handler.handler(load_event("health.json"), make_context())
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "healthy"
    assert body["request_id"] == "test-request-id"  # taken from the Lambda context


def test_recommendation_event(load_event):
    response = lambda_handler.handler(load_event("recommendations.json"), make_context("rec-1"))
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["request_id"] == "rec-1"
    assert len(body["recommendations"]) == 3
    assert body["recommendations"][0]["candidate_id"] == "U161"


def test_base64_encoded_body(load_event):
    event = load_event("recommendations.json")
    event["body"] = base64.b64encode(event["body"].encode()).decode()
    event["isBase64Encoded"] = True
    assert lambda_handler.handler(event, make_context())["statusCode"] == 200


def test_invalid_body_event_returns_400(load_event):
    event = load_event("recommendations.json")
    event["body"] = "{not-json"
    response = lambda_handler.handler(event, make_context())
    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["code"] == "INVALID_JSON"


def test_validation_error_event_returns_422(load_event):
    event = load_event("recommendations.json")
    event["body"] = json.dumps({"user_id": "U001", "age": "twenty"})
    assert lambda_handler.handler(event, make_context())["statusCode"] == 422


def test_first_invocation_flag_and_structured_log(load_event, monkeypatch):
    captured: list[dict] = []
    real_log_event = lambda_handler.log_event

    def spy(event, level=logging.INFO, **fields):
        record = real_log_event(event, level, **fields)
        captured.append(json.loads(json.dumps(record, default=str)))  # must be JSON-serialisable
        return record

    monkeypatch.setattr(lambda_handler, "log_event", spy)
    lambda_handler.handler(load_event("health.json"), make_context("first"))
    lambda_handler.handler(load_event("health.json"), make_context("second"))

    invocations = [r for r in captured if r["event"] == "lambda_invocation"]
    assert [r["first_invocation_in_env"] for r in invocations] == [True, False]
    assert [r["invocation_number_in_env"] for r in invocations] == [1, 2]
    assert invocations[0]["module_init_ms"] is not None
    assert invocations[1]["module_init_ms"] is None
    assert invocations[0]["route"] == "GET /health"
    assert invocations[0]["status_code"] == 200
    assert invocations[0]["memory_limit_mb"] == 512


def test_module_init_duration_recorded():
    assert lambda_handler.INIT_DURATION_MS >= 0
    assert lambda_handler._PROFILE_COUNT >= 50


def test_route_helper_handles_unknown_event_shape():
    assert lambda_handler._route({}) == "UNKNOWN UNKNOWN"
    assert lambda_handler._route({"httpMethod": "GET", "path": "/x"}) == "GET /x"
