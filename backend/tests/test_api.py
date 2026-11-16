"""API integration tests through FastAPI's TestClient (real HTTP semantics)."""

from __future__ import annotations


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["profiles_loaded"] >= 50
    assert body["scoring_weights"]["age"] == 30
    assert response.headers["X-Request-ID"] == body["request_id"]
    assert float(response.headers["X-Response-Time-Ms"]) >= 0


def test_valid_recommendation_request(client, payload):
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["user_id"] == "U001"
    assert len(body["recommendations"]) == 5
    assert "message" not in body  # only present when there are no matches


def test_response_structure(client, payload):
    body = client.post("/recommendations", json=payload).json()
    assert set(body) == {
        "status",
        "user_id",
        "total_candidates",
        "candidates_after_filters",
        "recommendations",
        "request_id",
    }
    rec = body["recommendations"][0]
    assert set(rec) == {
        "candidate_id",
        "compatibility_score",
        "age",
        "city",
        "education",
        "common_interests",
        "reasons",
        "score_breakdown",
    }
    assert set(rec["score_breakdown"]) == {"age", "location", "education", "interests"}
    assert isinstance(rec["compatibility_score"], int)


def test_results_respect_preferences_and_exclude_self(client, payload):
    payload["top_n"] = 20
    body = client.post("/recommendations", json=payload).json()
    ids = [r["candidate_id"] for r in body["recommendations"]]
    assert "U001" not in ids
    assert all(23 <= r["age"] <= 29 for r in body["recommendations"])
    scores = [r["compatibility_score"] for r in body["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_request_id_header_is_propagated(client, payload):
    response = client.post("/recommendations", json=payload, headers={"X-Request-ID": "demo-123"})
    assert response.json()["request_id"] == "demo-123"
    assert response.headers["X-Request-ID"] == "demo-123"


def test_no_matches_returns_200_with_message(client, payload):
    payload["preferences"] = {"min_age": 90, "max_age": 100}
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert "No candidates matched" in body["message"]


def test_invalid_json_returns_400(client):
    response = client.post("/recommendations", content="{bad json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INVALID_JSON"
    assert body["request_id"]


def test_missing_body_returns_400(client):
    response = client.post("/recommendations")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_BODY"


def test_json_array_body_returns_400(client):
    response = client.post("/recommendations", json=[1, 2, 3])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_BODY"


def test_field_errors_return_422_with_details(client, payload):
    payload["age"] = 12
    del payload["city"]
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    fields = {d["field"] for d in error["details"]}
    assert {"age", "city"} <= fields


def test_invalid_age_range_returns_422(client, payload):
    payload["preferences"] = {"min_age": 30, "max_age": 20}
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 422
    assert "min_age" in response.json()["error"]["details"][0]["message"]


def test_unknown_route_returns_404_in_standard_format(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_wrong_method_returns_405(client):
    response = client.get("/recommendations")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_cors_preflight(client):
    response = client.options(
        "/recommendations",
        headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ("*", "http://localhost:5500")
