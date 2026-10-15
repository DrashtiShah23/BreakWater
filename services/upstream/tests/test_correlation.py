"""Correlation identifier propagation for later Envoy log joining."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_propagates_supplied_request_id(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/items",
        headers={"x-request-id": "corr-abc-123"},
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "corr-abc-123"
    assert response.json()["request_id"] == "corr-abc-123"


def test_generates_request_id_when_missing(api_client: TestClient) -> None:
    response = api_client.get("/api/v2/items")
    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    assert request_id
    assert response.json()["request_id"] == request_id


def test_correlation_on_injected_error(api_client: TestClient) -> None:
    api_client.post("/__test__/errors", json={"mode": "http_500", "count": 1})
    response = api_client.get(
        "/api/v1/items",
        headers={"x-request-id": "err-corr-9"},
    )
    assert response.status_code == 500
    assert response.headers["x-request-id"] == "err-corr-9"
    assert response.json()["request_id"] == "err-corr-9"


def test_correlation_on_health(api_client: TestClient) -> None:
    response = api_client.get("/health", headers={"x-request-id": "health-1"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "health-1"
    assert response.json()["request_id"] == "health-1"
