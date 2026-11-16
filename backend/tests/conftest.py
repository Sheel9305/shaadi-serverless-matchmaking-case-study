"""Shared pytest fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app
from models import CandidateProfile, RecommendationRequest

EVENTS_DIR = Path(__file__).resolve().parents[1] / "events"

VALID_PAYLOAD = {
    "user_id": "U001",
    "age": 25,
    "city": "Ahmedabad",
    "education": "Engineering",
    "interests": ["music", "travel", "technology"],
    "preferences": {"min_age": 23, "max_age": 29, "preferred_city": "Ahmedabad"},
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def payload() -> dict:
    """A fresh, mutable copy of the README example request."""
    return copy.deepcopy(VALID_PAYLOAD)


@pytest.fixture
def make_request():
    def _make(**overrides) -> RecommendationRequest:
        data = copy.deepcopy(VALID_PAYLOAD)
        prefs = overrides.pop("preferences", None)
        if prefs is not None:
            data["preferences"] = prefs
        data.update(overrides)
        return RecommendationRequest.model_validate(data)

    return _make


@pytest.fixture
def make_candidate():
    def _make(candidate_id="C1", age=25, city="Ahmedabad", education="Engineering", interests=("music",)):
        return CandidateProfile(
            candidate_id=candidate_id, age=age, city=city, education=education, interests=list(interests)
        )

    return _make


@pytest.fixture
def load_event():
    def _load(name: str) -> dict:
        return json.loads((EVENTS_DIR / name).read_text(encoding="utf-8"))

    return _load
