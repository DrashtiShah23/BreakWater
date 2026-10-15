"""Health / liveness semantics for later Envoy active checks."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_healthy_by_default(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["healthy"] is True
    assert body["instance_id"] == "api-test-1"


def test_live_always_alive(api_client: TestClient) -> None:
    api_client.post("/__test__/health", json={"healthy": False})
    live = api_client.get("/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    health = api_client.get("/health")
    assert health.status_code == 503
    assert health.json()["reason"] == "intentional_unhealthy"


def test_unhealthy_then_recovery(api_client: TestClient) -> None:
    bad = api_client.post("/__test__/health", json={"healthy": False})
    assert bad.status_code == 200
    assert api_client.get("/health").status_code == 503

    reset = api_client.post("/__test__/reset")
    assert reset.status_code == 200
    recovered = api_client.get("/health")
    assert recovered.status_code == 200
    assert recovered.json()["healthy"] is True


def test_status_surface_health(status_client: TestClient) -> None:
    response = status_client.get("/health")
    assert response.status_code == 200
    assert response.json()["surface"] == "status"
