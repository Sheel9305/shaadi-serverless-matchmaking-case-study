"""Tests for the Pydantic data models and the synthetic dataset."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from models import EDUCATION_CATEGORIES, CandidateProfile, Preferences, RecommendationRequest
from repository import DEFAULT_DATA_PATH, JsonProfileRepository, RepositoryError


def test_valid_request_uses_defaults(payload):
    del payload["preferences"]
    req = RecommendationRequest.model_validate(payload)
    assert req.top_n == 5
    assert req.preferences.min_age == 18
    assert req.preferences.max_age == 100
    assert req.preferences.preferred_city is None


def test_interests_are_normalised_to_lowercase(payload):
    payload["interests"] = ["  Music ", "TRAVEL"]
    req = RecommendationRequest.model_validate(payload)
    assert req.interests == ["music", "travel"]


def test_city_whitespace_is_collapsed(payload):
    payload["city"] = "  New   Delhi "
    assert RecommendationRequest.model_validate(payload).city == "New Delhi"


def test_extra_fields_are_rejected(payload):
    payload["password"] = "not-allowed"
    with pytest.raises(ValidationError):
        RecommendationRequest.model_validate(payload)


def test_preferences_min_greater_than_max_rejected():
    with pytest.raises(ValidationError, match="min_age must be less than or equal"):
        Preferences(min_age=30, max_age=25)


def test_city_required_needs_preferred_city():
    with pytest.raises(ValidationError, match="preferred_city is required"):
        Preferences(city_required=True)


def test_candidate_profile_is_immutable(make_candidate):
    candidate = make_candidate()
    with pytest.raises(ValidationError):
        candidate.age = 40


# --- Synthetic dataset --------------------------------------------------------


def test_dataset_file_is_valid_json_and_marked_synthetic():
    document = json.loads(DEFAULT_DATA_PATH.read_text(encoding="utf-8"))
    assert document["synthetic"] is True
    assert len(document["profiles"]) >= 50


def test_every_dataset_profile_is_valid():
    profiles = JsonProfileRepository().list_candidates()
    ids = [p.candidate_id for p in profiles]
    assert len(ids) == len(set(ids)), "candidate IDs must be unique"
    assert all(p.education in EDUCATION_CATEGORIES for p in profiles)
    assert all(18 <= p.age <= 100 for p in profiles)
    assert len({p.city for p in profiles}) >= 5, "dataset should cover several cities"


def test_dataset_contains_demo_user_for_exclusion_check():
    ids = {p.candidate_id for p in JsonProfileRepository().list_candidates()}
    assert "U001" in ids


def test_repository_missing_file(tmp_path):
    with pytest.raises(RepositoryError, match="not found"):
        JsonProfileRepository(tmp_path / "missing.json").list_candidates()


def test_repository_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(RepositoryError, match="not valid JSON"):
        JsonProfileRepository(bad).list_candidates()


def test_repository_wrong_shape(tmp_path):
    bad = tmp_path / "shape.json"
    bad.write_text(json.dumps({"items": []}), encoding="utf-8")
    with pytest.raises(RepositoryError, match="'profiles' list"):
        JsonProfileRepository(bad).list_candidates()


def test_repository_caches_profiles(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(
        json.dumps(
            {"profiles": [{"candidate_id": "X1", "age": 30, "city": "Pune", "education": "Arts", "interests": ["art"]}]}
        ),
        encoding="utf-8",
    )
    repo = JsonProfileRepository(path)
    first = repo.list_candidates()
    path.unlink()  # a second read would fail, so this proves the cache is used
    assert repo.list_candidates() is first
    assert isinstance(first[0], CandidateProfile)
