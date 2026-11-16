"""Edge cases and failure handling."""

from __future__ import annotations

from fastapi.testclient import TestClient

import app as app_module
import repository
from repository import JsonProfileRepository, RepositoryError


def test_unexpected_exception_returns_500_without_leaking_details(monkeypatch, payload):
    def explode(*_args, **_kwargs):
        raise ZeroDivisionError("secret internal detail")

    monkeypatch.setattr(app_module, "recommend", explode)
    client = TestClient(app_module.app, raise_server_exceptions=False)
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "secret" not in response.text


def test_data_unavailable_returns_503(monkeypatch, client):
    class BrokenRepo(JsonProfileRepository):
        def list_candidates(self):
            raise RepositoryError("file missing")

    monkeypatch.setattr(app_module, "get_repository", lambda: BrokenRepo())
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATA_UNAVAILABLE"


def test_custom_profiles_path_via_environment(monkeypatch, tmp_path):
    data = tmp_path / "profiles.json"
    data.write_text(
        '{"profiles": [{"candidate_id": "Z9", "age": 30, "city": "Pune", "education": "Law", "interests": ["art"]}]}',
        encoding="utf-8",
    )
    monkeypatch.setenv("PROFILES_PATH", str(data))
    repository.get_repository.cache_clear()
    try:
        repo = repository.get_repository()
        assert [p.candidate_id for p in repo.list_candidates()] == ["Z9"]
    finally:
        repository.get_repository.cache_clear()


def test_unsupported_data_backend(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "oracle")
    repository.get_repository.cache_clear()
    try:
        try:
            repository.get_repository()
            raise AssertionError("expected RepositoryError")
        except RepositoryError as exc:
            assert "Unsupported DATA_BACKEND" in str(exc)
    finally:
        repository.get_repository.cache_clear()


def test_single_interest_and_max_top_n(client, payload):
    payload["interests"] = ["music"]
    payload["top_n"] = 20
    payload["preferences"] = {}
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 20


def test_unicode_city_is_accepted(client, payload):
    payload["city"] = "अहमदाबाद"
    payload["preferences"] = {"preferred_city": "अहमदाबाद"}
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200


def test_null_preferences_rejected(client, payload):
    payload["preferences"] = None
    assert client.post("/recommendations", json=payload).status_code == 422


def test_large_body_with_extra_keys_rejected(client, payload):
    payload.update({f"k{i}": i for i in range(200)})
    assert client.post("/recommendations", json=payload).status_code == 422


def test_city_required_through_api(client, payload):
    payload["preferences"] = {"min_age": 18, "max_age": 100, "preferred_city": "Pune", "city_required": True}
    payload["top_n"] = 20
    body = client.post("/recommendations", json=payload).json()
    assert body["recommendations"], "dataset should contain Pune profiles"
    assert all(r["city"] == "Pune" for r in body["recommendations"])
