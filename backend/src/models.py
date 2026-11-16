"""Data models (request, response and stored profile) for the recommendation API.

Pydantic v2 is used so that validation rules live in ONE place and FastAPI can
reuse them automatically. Numeric fields use ``strict=True`` so that values such
as ``"25"`` (a string) or ``true`` (a boolean) are rejected instead of being
silently converted.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# --- Domain constants (shared with the frontend dropdowns and the docs) -------
MIN_AGE = 18
MAX_AGE = 100
MAX_INTERESTS = 10
MAX_TOP_N = 20
DEFAULT_TOP_N = 5

EDUCATION_CATEGORIES: tuple[str, ...] = (
    "Engineering",
    "Medicine",
    "Science",
    "Commerce",
    "Management",
    "Arts",
    "Law",
)
EducationCategory = Literal["Engineering", "Medicine", "Science", "Commerce", "Management", "Arts", "Law"]


def _clean_text(value: str) -> str:
    """Trim whitespace and collapse internal spaces."""
    return " ".join(value.split())


class Preferences(BaseModel):
    """What the requesting user is looking for."""

    model_config = ConfigDict(extra="forbid")

    min_age: int = Field(MIN_AGE, ge=MIN_AGE, le=MAX_AGE, strict=True)
    max_age: int = Field(MAX_AGE, ge=MIN_AGE, le=MAX_AGE, strict=True)
    preferred_city: str | None = Field(None, min_length=2, max_length=50)
    preferred_education: EducationCategory | None = None
    # When true, candidates outside preferred_city are removed (hard filter)
    # instead of only receiving a lower score (soft preference).
    city_required: bool = Field(False, strict=True)

    @field_validator("preferred_city")
    @classmethod
    def _normalise_city(cls, value: str | None) -> str | None:
        return _clean_text(value) if value is not None else None

    @model_validator(mode="after")
    def _check_age_range(self) -> Preferences:
        if self.min_age > self.max_age:
            raise ValueError("preferences.min_age must be less than or equal to preferences.max_age")
        if self.city_required and not self.preferred_city:
            raise ValueError("preferences.preferred_city is required when city_required is true")
        return self


class RecommendationRequest(BaseModel):
    """Body of POST /recommendations."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(..., ge=MIN_AGE, le=MAX_AGE, strict=True)
    city: str = Field(..., min_length=2, max_length=50)
    education: EducationCategory
    interests: list[str] = Field(..., min_length=1, max_length=MAX_INTERESTS)
    preferences: Preferences = Field(default_factory=Preferences)
    top_n: int = Field(DEFAULT_TOP_N, ge=1, le=MAX_TOP_N, strict=True)

    @field_validator("city")
    @classmethod
    def _normalise_city(cls, value: str) -> str:
        return _clean_text(value)

    @field_validator("interests")
    @classmethod
    def _normalise_interests(cls, values: list[str]) -> list[str]:
        cleaned = [_clean_text(v).lower() for v in values]
        if any(not v for v in cleaned):
            raise ValueError("interests must not contain empty values")
        if any(len(v) > 30 for v in cleaned):
            raise ValueError("each interest must be at most 30 characters")
        duplicates = sorted({v for v in cleaned if cleaned.count(v) > 1})
        if duplicates:
            raise ValueError(f"duplicate interests are not allowed: {', '.join(duplicates)}")
        return cleaned


class CandidateProfile(BaseModel):
    """A synthetic profile stored in the dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(..., min_length=1, max_length=20)
    age: int = Field(..., ge=MIN_AGE, le=MAX_AGE)
    city: str
    education: EducationCategory
    interests: list[str] = Field(..., min_length=1)


class ScoreBreakdown(BaseModel):
    age: float
    location: float
    education: float
    interests: float


class Recommendation(BaseModel):
    candidate_id: str
    compatibility_score: int = Field(..., ge=0, le=100)
    age: int
    city: str
    education: str
    common_interests: list[str]
    reasons: list[str]
    score_breakdown: ScoreBreakdown


class RecommendationResponse(BaseModel):
    status: Literal["success"] = "success"
    user_id: str
    total_candidates: int
    candidates_after_filters: int
    recommendations: list[Recommendation]
    message: str | None = None
    request_id: str
