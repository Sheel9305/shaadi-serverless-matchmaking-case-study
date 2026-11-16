"""Explainable, rules-based compatibility scoring.

This is NOT a machine-learning model. It is a transparent weighted score, so
every point can be explained to a user (and to a viva examiner).

Compatibility score (0-100) = age + location + education + interests

    Component   Max points   Rule
    ---------   ----------   ------------------------------------------------
    age              30      30 * max(0, 1 - |age gap| / 10)
    location         25      25 if city == preferred city (or the user's own city
                             when no preference is given); 10 if the candidate
                             lives in the user's own city but the user prefers
                             another city; otherwise 0
    education        15      15 if same category as the target education;
                             8 if in the same broad field group; otherwise 0
    interests        30      30 * |common| / min(|user|, |candidate|)
                             (the "overlap coefficient")

Hard filters (candidate removed before scoring):
    * candidate_id == requesting user_id   (never recommend a user to themself)
    * candidate age outside [min_age, max_age]
    * candidate city != preferred_city      (only when city_required is true)
"""

from __future__ import annotations

from dataclasses import dataclass

from models import CandidateProfile, Recommendation, RecommendationRequest, ScoreBreakdown

WEIGHTS: dict[str, int] = {"age": 30, "location": 25, "education": 15, "interests": 30}
AGE_GAP_TOLERANCE_YEARS = 10
LOCATION_OWN_CITY_POINTS = 10
EDUCATION_RELATED_POINTS = 8

# Broad field groups used for "related education" partial credit.
EDUCATION_GROUPS: dict[str, str] = {
    "Engineering": "STEM",
    "Science": "STEM",
    "Medicine": "STEM",
    "Commerce": "Business",
    "Management": "Business",
    "Arts": "Humanities",
    "Law": "Humanities",
}

assert sum(WEIGHTS.values()) == 100, "Scoring weights must add up to 100"

NO_MATCH_MESSAGE = "No candidates matched your preferences. Try widening the age range or relaxing the city filter."


@dataclass(frozen=True)
class RecommendationResult:
    total_candidates: int
    candidates_after_filters: int
    recommendations: list[Recommendation]

    @property
    def message(self) -> str | None:
        return None if self.recommendations else NO_MATCH_MESSAGE


def _same_city(a: str | None, b: str | None) -> bool:
    return a is not None and b is not None and a.casefold() == b.casefold()


def passes_filters(request: RecommendationRequest, candidate: CandidateProfile) -> bool:
    prefs = request.preferences
    if candidate.candidate_id.casefold() == request.user_id.casefold():
        return False
    if not prefs.min_age <= candidate.age <= prefs.max_age:
        return False
    if prefs.city_required and not _same_city(candidate.city, prefs.preferred_city):
        return False
    return True


def score_age(user_age: int, candidate_age: int) -> float:
    gap = abs(user_age - candidate_age)
    return WEIGHTS["age"] * max(0.0, 1 - gap / AGE_GAP_TOLERANCE_YEARS)


def score_location(request: RecommendationRequest, candidate: CandidateProfile) -> float:
    target_city = request.preferences.preferred_city or request.city
    if _same_city(candidate.city, target_city):
        return float(WEIGHTS["location"])
    if _same_city(candidate.city, request.city):
        return float(LOCATION_OWN_CITY_POINTS)
    return 0.0


def score_education(request: RecommendationRequest, candidate: CandidateProfile) -> float:
    target = request.preferences.preferred_education or request.education
    if candidate.education == target:
        return float(WEIGHTS["education"])
    if EDUCATION_GROUPS.get(candidate.education) == EDUCATION_GROUPS.get(target):
        return float(EDUCATION_RELATED_POINTS)
    return 0.0


def common_interests(user_interests: list[str], candidate_interests: list[str]) -> list[str]:
    candidate_set = {i.lower() for i in candidate_interests}
    return sorted(i for i in set(user_interests) if i in candidate_set)


def score_interests(user_interests: list[str], candidate_interests: list[str]) -> float:
    if not user_interests or not candidate_interests:
        return 0.0
    shared = len(common_interests(user_interests, candidate_interests))
    return WEIGHTS["interests"] * shared / min(len(set(user_interests)), len(set(candidate_interests)))


def build_reasons(
    request: RecommendationRequest,
    candidate: CandidateProfile,
    breakdown: ScoreBreakdown,
    shared: list[str],
) -> list[str]:
    reasons: list[str] = []
    gap = abs(request.age - candidate.age)
    if gap == 0:
        reasons.append("Same age")
    elif breakdown.age >= WEIGHTS["age"] * 0.7:
        reasons.append(f"Similar age ({gap} year{'s' if gap != 1 else ''} apart)")

    if breakdown.location == WEIGHTS["location"]:
        if request.preferences.preferred_city:
            reasons.append(f"Matches location preference ({candidate.city})")
        else:
            reasons.append(f"Lives in the same city ({candidate.city})")
    elif breakdown.location > 0:
        reasons.append(f"Lives in your city ({candidate.city})")

    if breakdown.education == WEIGHTS["education"]:
        reasons.append(f"Same education background ({candidate.education})")
    elif breakdown.education > 0:
        reasons.append(f"Related education field ({candidate.education})")

    if shared:
        label = "Shared interest" if len(shared) == 1 else "Similar interests"
        reasons.append(f"{label}: {', '.join(shared)}")

    if not reasons:
        reasons.append("Within your preferred age range")
    return reasons


def score_candidate(request: RecommendationRequest, candidate: CandidateProfile) -> Recommendation:
    shared = common_interests(request.interests, candidate.interests)
    breakdown = ScoreBreakdown(
        age=round(score_age(request.age, candidate.age), 2),
        location=round(score_location(request, candidate), 2),
        education=round(score_education(request, candidate), 2),
        interests=round(score_interests(request.interests, candidate.interests), 2),
    )
    total = breakdown.age + breakdown.location + breakdown.education + breakdown.interests
    score = max(0, min(100, round(total)))
    return Recommendation(
        candidate_id=candidate.candidate_id,
        compatibility_score=score,
        age=candidate.age,
        city=candidate.city,
        education=candidate.education,
        common_interests=shared,
        reasons=build_reasons(request, candidate, breakdown, shared),
        score_breakdown=breakdown,
    )


def recommend(request: RecommendationRequest, candidates: list[CandidateProfile]) -> RecommendationResult:
    """Filter -> score -> sort -> top N."""
    eligible = [c for c in candidates if passes_filters(request, c)]
    scored = [score_candidate(request, c) for c in eligible]
    # Highest score first; ties broken by candidate_id so results are deterministic.
    scored.sort(key=lambda r: (-r.compatibility_score, r.candidate_id))
    return RecommendationResult(
        total_candidates=len(candidates),
        candidates_after_filters=len(eligible),
        recommendations=scored[: request.top_n],
    )
