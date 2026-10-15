"""Failure-injection controls and isolation from normal traffic."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient


def test_injected_latency(api_client: TestClient) -> None:
    cfg = api_client.post("/__test__/latency", json={"delay_ms": 100})
    assert cfg.status_code == 200
    started = time.perf_counter()
    response = api_client.get("/api/v1/items")
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed >= 0.09
    assert response.headers["x-upstream-behavior"] == "latency"
    assert response.headers["x-upstream-injected-latency-ms"] == "100"


def test_controlled_5xx_then_exhausts(api_client: TestClient) -> None:
    cfg = api_client.post(
        "/__test__/errors",
        json={"mode": "http_500", "count": 2},
    )
    assert cfg.status_code == 200
    first = api_client.get("/api/v1/items")
    second = api_client.get("/api/v1/items")
    third = api_client.get("/api/v1/items")
    assert first.status_code == 500
    assert first.json()["behavior"] == "http_500"
    assert second.status_code == 500
    assert third.status_code == 200
    assert third.json()["api_version"] == "v1"


def test_controlled_503_until_reset(api_client: TestClient) -> None:
    api_client.post("/__test__/errors", json={"mode": "http_503"})
    assert api_client.get("/api/v2/items").status_code == 503
    assert api_client.get("/api/v2/items").status_code == 503
    api_client.post("/__test__/reset")
    assert api_client.get("/api/v2/items").status_code == 200


def test_errors_do_not_override_health_readiness_semantics(api_client: TestClient) -> None:
    api_client.post("/__test__/errors", json={"mode": "http_500"})
    # /health remains a readiness signal, not an injected-error channel.
    assert api_client.get("/health").status_code == 200
    assert api_client.get("/api/v1/items").status_code == 500


def test_invalid_latency_rejected(api_client: TestClient) -> None:
    response = api_client.post("/__test__/latency", json={"delay_ms": 50_000})
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "invalid_test_control"


def test_invalid_error_mode_rejected(api_client: TestClient) -> None:
    response = api_client.post("/__test__/errors", json={"mode": "explode"})
    assert response.status_code == 422


def test_invalid_crash_without_confirm(api_client: TestClient) -> None:
    response = api_client.post("/__test__/crash", json={"confirm": False})
    assert response.status_code == 422


def test_controls_disabled_absent(api_client_controls_disabled: TestClient) -> None:
    assert api_client_controls_disabled.get("/__test__/state").status_code == 404
    assert (
        api_client_controls_disabled.post("/__test__/latency", json={"delay_ms": 1}).status_code
        == 404
    )
    # Normal data path still works.
    assert api_client_controls_disabled.get("/api/v1/items").status_code == 200
    assert api_client_controls_disabled.get("/health").status_code == 200


def test_get_state(api_client: TestClient) -> None:
    api_client.post("/__test__/latency", json={"delay_ms": 25})
    state = api_client.get("/__test__/state")
    assert state.status_code == 200
    body = state.json()
    assert body["state"]["latency_ms"] == 25
    assert body["limits"]["max_latency_ms"] == 5_000
