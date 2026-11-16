"""Unit tests for the explainable scoring algorithm."""

from __future__ import annotations

import pytest

import recommendation_service as svc
from recommendation_service import WEIGHTS, recommend, score_candidate
from repository import JsonProfileRepository


def test_weights_sum_to_100():
    assert sum(WEIGHTS.values()) == 100
    assert WEIGHTS == {"age": 30, "location": 25, "education": 15, "interests": 30}


def test_perfect_match_scores_100(make_request, make_candidate):
    req = make_request()
    cand = make_candidate(
        age=25, city="Ahmedabad", education="Engineering", interests=["music", "travel", "technology"]
    )
    rec = score_candidate(req, cand)
    assert rec.compatibility_score == 100
    assert rec.score_breakdown.model_dump() == {"age": 30, "location": 25, "education": 15, "interests": 30}
    assert "Same age" in rec.reasons
    assert "Matches location preference (Ahmedabad)" in rec.reasons


def test_worst_case_scores_0(make_request, make_candidate):
    req = make_request(preferences={"min_age": 18, "max_age": 100})
    cand = make_candidate(age=40, city="Chennai", education="Arts", interests=["yoga"])
    rec = score_candidate(req, cand)
    assert rec.compatibility_score == 0
    assert rec.reasons == ["Within your preferred age range"]


@pytest.mark.parametrize("gap,expected", [(0, 30), (1, 27), (5, 15), (10, 0), (15, 0)])
def test_age_score(gap, expected):
    assert svc.score_age(25, 25 + gap) == pytest.approx(expected)


def test_location_scoring(make_request, make_candidate):
    req = make_request(city="Ahmedabad", preferences={"preferred_city": "Mumbai"})
    assert svc.score_location(req, make_candidate(city="mumbai")) == 25  # case-insensitive
    assert svc.score_location(req, make_candidate(city="Ahmedabad")) == svc.LOCATION_OWN_CITY_POINTS
    assert svc.score_location(req, make_candidate(city="Pune")) == 0


def test_location_defaults_to_users_city(make_request, make_candidate):
    req = make_request(preferences={})
    rec = score_candidate(req, make_candidate(city="Ahmedabad"))
    assert rec.score_breakdown.location == 25
    assert "Lives in the same city (Ahmedabad)" in rec.reasons


def test_education_scoring(make_request, make_candidate):
    req = make_request(education="Engineering")
    assert svc.score_education(req, make_candidate(education="Engineering")) == 15
    assert svc.score_education(req, make_candidate(education="Science")) == svc.EDUCATION_RELATED_POINTS
    assert svc.score_education(req, make_candidate(education="Law")) == 0


def test_preferred_education_overrides_own(make_request, make_candidate):
    req = make_request(education="Engineering", preferences={"preferred_education": "Medicine"})
    assert svc.score_education(req, make_candidate(education="Medicine")) == 15


def test_interest_overlap_coefficient():
    assert svc.score_interests(["music", "travel"], ["music", "travel", "art", "yoga"]) == 30
    assert svc.score_interests(["music", "travel"], ["music", "art"]) == 15
    assert svc.score_interests(["music"], ["art"]) == 0
    assert svc.score_interests([], ["art"]) == 0


def test_common_interests_sorted_and_case_insensitive():
    assert svc.common_interests(["travel", "music"], ["Music", "TRAVEL", "art"]) == ["music", "travel"]


def test_excludes_requesting_user(make_request, make_candidate):
    req = make_request(user_id="U001")
    result = recommend(req, [make_candidate("U001"), make_candidate("u001"), make_candidate("U002")])
    assert [r.candidate_id for r in result.recommendations] == ["U002"]


def test_age_filter_is_inclusive(make_request, make_candidate):
    req = make_request(preferences={"min_age": 23, "max_age": 29})
    cands = [make_candidate(f"A{a}", age=a) for a in (22, 23, 26, 29, 30)]
    ids = {r.candidate_id for r in recommend(req, cands).recommendations}
    assert ids == {"A23", "A26", "A29"}


def test_city_required_is_a_hard_filter(make_request, make_candidate):
    req = make_request(preferences={"preferred_city": "Pune", "city_required": True})
    result = recommend(req, [make_candidate("P1", city="Pune"), make_candidate("A1", city="Ahmedabad")])
    assert [r.candidate_id for r in result.recommendations] == ["P1"]
    assert result.candidates_after_filters == 1


def test_city_preference_without_required_is_soft(make_request, make_candidate):
    req = make_request(preferences={"preferred_city": "Pune"})
    result = recommend(req, [make_candidate("P1", city="Pune"), make_candidate("C1", city="Chennai")])
    assert {r.candidate_id for r in result.recommendations} == {"P1", "C1"}


def test_results_sorted_descending_with_deterministic_ties(make_request, make_candidate):
    req = make_request(top_n=10)
    cands = [
        make_candidate("B", age=29, city="Chennai", education="Arts", interests=["yoga"]),
        make_candidate("Z", age=25, interests=["music", "travel", "technology"]),
        make_candidate("A", age=29, city="Chennai", education="Arts", interests=["yoga"]),
        make_candidate("M", age=27, interests=["music"]),
    ]
    recs = recommend(req, cands).recommendations
    scores = [r.compatibility_score for r in recs]
    assert scores == sorted(scores, reverse=True)
    assert [r.candidate_id for r in recs][:2] == ["Z", "M"]
    assert [r.candidate_id for r in recs][2:] == ["A", "B"]  # equal scores -> ID order


def test_top_n_limits_results(make_request):
    candidates = JsonProfileRepository().list_candidates()
    for n in (1, 3, 5):
        result = recommend(make_request(top_n=n, preferences={}), candidates)
        assert len(result.recommendations) == n


def test_no_matching_candidates(make_request, make_candidate):
    req = make_request(preferences={"min_age": 60, "max_age": 70})
    result = recommend(req, [make_candidate(age=25)])
    assert result.recommendations == []
    assert result.candidates_after_filters == 0
    assert result.message == svc.NO_MATCH_MESSAGE


def test_empty_dataset(make_request):
    result = recommend(make_request(), [])
    assert result.total_candidates == 0 and result.recommendations == []


def test_scores_always_within_bounds_on_full_dataset(make_request):
    candidates = JsonProfileRepository().list_candidates()
    for city in ("Ahmedabad", "Mumbai", "Nowhere"):
        req = make_request(city=city, preferences={}, top_n=20)
        for rec in recommend(req, candidates).recommendations:
            assert 0 <= rec.compatibility_score <= 100
            assert rec.reasons, "every recommendation must explain itself"


def test_readme_example_top_result(make_request):
    """Guards the example response documented in README.md."""
    result = recommend(make_request(top_n=3), JsonProfileRepository().list_candidates())
    top = result.recommendations[0]
    assert (top.candidate_id, top.compatibility_score) == ("U161", 97)
    assert [r.candidate_id for r in result.recommendations] == ["U161", "U162", "U133"]
