"""Versioned items API behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_v1_items(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/items")
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["instance_id"] == "api-test-1"
    assert body["surface"] == "api"
    assert body["count"] == 2
    assert all(item["version"] == "v1" for item in body["items"])
    assert "sku" not in body["items"][0]
    assert response.headers["x-upstream-instance"] == "api-test-1"
    assert response.headers["x-upstream-surface"] == "api"


def test_v2_items(api_client: TestClient) -> None:
    response = api_client.get("/api/v2/items")
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v2"
    assert body["count"] == 3
    assert all("sku" in item for item in body["items"])
    assert all(item["version"] == "v2" for item in body["items"])


def test_status_surface_has_status_not_items(status_client: TestClient) -> None:
    assert status_client.get("/api/v1/status").status_code == 200
    assert status_client.get("/api/v1/items").status_code == 404
    assert status_client.get("/api/v2/items").status_code == 404


def test_api_surface_has_items_not_status(api_client: TestClient) -> None:
    assert api_client.get("/api/v1/items").status_code == 200
    assert api_client.get("/api/v1/status").status_code == 404
