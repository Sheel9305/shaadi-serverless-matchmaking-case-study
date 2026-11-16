"""Data access layer.

The recommendation service only depends on the small ``ProfileRepository``
interface below. Today the data comes from a synthetic JSON file that is
packaged inside the Lambda deployment artefact (no database cost). Because the
service never touches the file directly, a DynamoDB-backed repository can be
added later without changing the scoring logic or the API.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

from models import CandidateProfile

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_profiles.json"


class RepositoryError(RuntimeError):
    """Raised when the profile data source cannot be read."""


class ProfileRepository(ABC):
    @abstractmethod
    def list_candidates(self) -> list[CandidateProfile]:
        """Return every candidate profile."""


class JsonProfileRepository(ProfileRepository):
    """Reads synthetic profiles from a JSON file (loaded once, then cached)."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_DATA_PATH
        self._profiles: list[CandidateProfile] | None = None

    def list_candidates(self) -> list[CandidateProfile]:
        if self._profiles is None:
            self._profiles = self._load()
        return self._profiles

    def _load(self) -> list[CandidateProfile]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RepositoryError(f"Profile data file not found: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Profile data file is not valid JSON: {self.path}") from exc

        raw_profiles = document.get("profiles") if isinstance(document, dict) else None
        if not isinstance(raw_profiles, list):
            raise RepositoryError("Profile data file must contain a 'profiles' list")
        return [CandidateProfile.model_validate(p) for p in raw_profiles]


class DynamoDBProfileRepository(ProfileRepository):  # pragma: no cover - future work
    """Placeholder showing where a DynamoDB implementation would plug in.

    A future version could use ``boto3.resource("dynamodb").Table(name).scan()``
    (or, better, a Query on a city/age index). It is intentionally not
    implemented, so the prototype stays free of database costs.
    """

    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def list_candidates(self) -> list[CandidateProfile]:
        raise NotImplementedError("DynamoDB storage is future work; see docs/04_student_architecture.md")


@lru_cache(maxsize=1)
def get_repository() -> ProfileRepository:
    """Build the configured repository once per process / Lambda environment.

    Caching here means that on AWS Lambda the JSON file is parsed during the
    first (cold) invocation and then reused by warm invocations.
    """
    backend = os.getenv("DATA_BACKEND", "json").lower()
    if backend == "json":
        return JsonProfileRepository(os.getenv("PROFILES_PATH") or None)
    if backend == "dynamodb":  # pragma: no cover - future work
        return DynamoDBProfileRepository(os.environ["PROFILES_TABLE"])
    raise RepositoryError(f"Unsupported DATA_BACKEND: {backend}")
