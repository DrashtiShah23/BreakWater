"""Edge path proofs: traffic traverses Envoy to the intended upstream (HTTPS + Host)."""

from __future__ import annotations

import httpx


def test_health_through_envoy(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/health", headers={"Host": api_host})
    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] is True
    assert body["instance_id"] == "api-1"
    assert body["surface"] == "api"
    assert response.headers.get("x-upstream-instance") == "api-1"


def test_v1_items_through_envoy(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/items", headers={"Host": api_host})
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["instance_id"] == "api-1"
    assert body["count"] == 2
    assert response.headers.get("x-upstream-instance") == "api-1"
    assert response.headers.get("x-upstream-surface") == "api"


def test_v2_items_through_envoy(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v2/items", headers={"Host": api_host})
    assert response.status_code == 200
    assert response.json()["api_version"] == "v2"


def test_correlation_id_preserved_through_envoy(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(
        f"{envoy_base}/api/v1/items",
        headers={"Host": api_host, "x-request-id": "edge-corr-m5"},
    )
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "edge-corr-m5"
    assert response.json()["request_id"] == "edge-corr-m5"


def test_envoy_generates_request_id_when_missing(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/items", headers={"Host": api_host})
    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id
    assert response.json()["request_id"] == request_id


def test_injected_5xx_passes_through_envoy(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    upstream_api_base: str,
    upstream_http: httpx.Client,
    require_stack: None,
) -> None:
    cfg = upstream_http.post(
        f"{upstream_api_base}/__test__/errors",
        json={"mode": "http_500", "count": 1},
    )
    assert cfg.status_code == 200

    response = http.get(f"{envoy_base}/api/v1/items", headers={"Host": api_host})
    assert response.status_code == 500
    assert response.json()["behavior"] == "http_500"
    assert response.headers.get("x-upstream-behavior") == "http_500"


def test_unknown_path_rejected_at_edge(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/does-not-exist", headers={"Host": api_host})
    assert response.status_code == 404
    assert "unknown_path" in response.text


def test_direct_upstream_still_works_without_envoy(
    upstream_http: httpx.Client, upstream_api_base: str, require_stack: None
) -> None:
    """Baseline path remains available for later edge-added latency comparison."""
    response = upstream_http.get(f"{upstream_api_base}/api/v1/items")
    assert response.status_code == 200
    assert response.json()["api_version"] == "v1"
