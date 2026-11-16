"""Field-level validation rules and error formatting."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from validation import classify_errors, format_errors, validate_request_payload


def _errors(payload) -> list[dict]:
    with pytest.raises(ValidationError) as exc_info:
        validate_request_payload(payload)
    return format_errors(exc_info.value.errors())


def test_valid_payload_passes(payload):
    req = validate_request_payload(payload)
    assert req.user_id == "U001"


@pytest.mark.parametrize("field", ["user_id", "age", "city", "education", "interests"])
def test_missing_required_field(payload, field):
    del payload[field]
    errors = _errors(payload)
    assert any(e["field"] == field and e["type"] == "missing" for e in errors)


@pytest.mark.parametrize("age", [17, 0, -5, 101, 150])
def test_age_out_of_range(payload, age):
    payload["age"] = age
    assert any(e["field"] == "age" for e in _errors(payload))


@pytest.mark.parametrize("age", ["25", 25.5, True, None, [25]])
def test_age_wrong_type(payload, age):
    payload["age"] = age
    assert any(e["field"] == "age" for e in _errors(payload))


def test_age_boundaries_are_accepted(payload):
    for age in (18, 100):
        payload["age"] = age
        payload["preferences"] = {"min_age": 18, "max_age": 100}
        assert validate_request_payload(payload).age == age


def test_invalid_age_range(payload):
    payload["preferences"] = {"min_age": 30, "max_age": 25}
    errors = _errors(payload)
    assert errors[0]["field"] == "preferences"
    assert "min_age must be less than or equal" in errors[0]["message"]


@pytest.mark.parametrize("prefs", [{"min_age": 10}, {"max_age": 120}, {"min_age": "20"}])
def test_invalid_preference_values(payload, prefs):
    payload["preferences"] = prefs
    assert any(e["field"].startswith("preferences.") for e in _errors(payload))


def test_empty_interests_rejected(payload):
    payload["interests"] = []
    assert any(e["field"] == "interests" for e in _errors(payload))


def test_blank_interest_value_rejected(payload):
    payload["interests"] = ["music", "   "]
    assert any("empty" in e["message"] for e in _errors(payload))


def test_duplicate_interests_rejected_case_insensitively(payload):
    payload["interests"] = ["Music", "music", "travel"]
    errors = _errors(payload)
    assert "duplicate interests are not allowed: music" in errors[0]["message"]


def test_too_many_interests_rejected(payload):
    payload["interests"] = [f"hobby{i}" for i in range(11)]
    assert any(e["field"] == "interests" for e in _errors(payload))


@pytest.mark.parametrize(
    "field,value",
    [
        ("interests", "music"),  # string instead of list
        ("interests", [1, 2]),  # numbers instead of strings
        ("city", 123),
        ("user_id", 1),
        ("preferences", "Ahmedabad"),
        ("education", "Astrology"),  # not an allowed category
        ("user_id", "U 001; DROP"),  # characters outside the allowed pattern
        ("top_n", 0),
        ("top_n", 21),
    ],
)
def test_unexpected_input_types_and_values(payload, field, value):
    payload[field] = value
    assert any(e["field"].split(".")[0] == field for e in _errors(payload))


def test_unknown_field_rejected(payload):
    payload["religion"] = "not collected"
    assert any(e["field"] == "religion" for e in _errors(payload))


def test_value_error_prefix_is_removed(payload):
    payload["interests"] = ["a", "a"]
    assert not _errors(payload)[0]["message"].startswith("Value error")


@pytest.mark.parametrize(
    "error,expected",
    [
        ({"type": "json_invalid", "loc": ("body", 5)}, (400, "INVALID_JSON")),
        ({"type": "missing", "loc": ("body",)}, (400, "MISSING_BODY")),
        ({"type": "model_attributes_type", "loc": ("body",)}, (400, "INVALID_BODY")),
        ({"type": "missing", "loc": ("body", "age")}, (422, "VALIDATION_ERROR")),
        ({"type": "int_type", "loc": ("body", "age")}, (422, "VALIDATION_ERROR")),
    ],
)
def test_classify_errors(error, expected):
    status, code, _ = classify_errors([error])
    assert (status, code) == expected
