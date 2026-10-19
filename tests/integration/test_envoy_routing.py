"""Milestone 5: host and path routing contract."""

from __future__ import annotations

import httpx


def test_api_host_routes_to_api_upstream(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/items", headers={"Host": api_host})
    assert response.status_code == 200
    body = response.json()
    assert body["surface"] == "api"
    assert body["instance_id"] in {"api-1", "api-2"}
    assert body["api_version"] == "v1"
    assert response.headers.get("x-upstream-surface") == "api"


def test_api_v2_path_routing(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v2/items", headers={"Host": api_host})
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v2"
    assert body["surface"] == "api"
    assert all("sku" in item for item in body["items"])


def test_status_host_routes_to_status_upstream(
    http: httpx.Client, envoy_base: str, status_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/status", headers={"Host": status_host})
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "status"
    assert body["surface"] == "status"
    assert body["instance_id"] == "status-1"
    assert response.headers.get("x-upstream-surface") == "status"
    assert response.headers.get("x-upstream-instance") == "status-1"


def test_status_host_health(
    http: httpx.Client, envoy_base: str, status_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/health", headers={"Host": status_host})
    assert response.status_code == 200
    assert response.json()["surface"] == "status"
    assert response.json()["instance_id"] == "status-1"


def test_api_host_cannot_reach_status_path(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/status", headers={"Host": api_host})
    assert response.status_code == 404
    assert "unknown_path" in response.text


def test_status_host_cannot_reach_items_path(
    http: httpx.Client, envoy_base: str, status_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/items", headers={"Host": status_host})
    assert response.status_code == 404
    assert "unknown_path" in response.text


def test_unknown_host_rejected(
    http: httpx.Client, envoy_base: str, require_stack: None
) -> None:
    response = http.get(
        f"{envoy_base}/api/v1/items",
        headers={"Host": "other.breakwater.local"},
    )
    assert response.status_code == 404
    assert "unknown_host" in response.text


def test_test_control_not_routed_via_envoy_api_host(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/__test__/state", headers={"Host": api_host})
    assert response.status_code == 404
    assert "unknown_path" in response.text


def test_test_control_not_routed_via_envoy_status_host(
    http: httpx.Client, envoy_base: str, status_host: str, require_stack: None
) -> None:
    response = http.post(
        f"{envoy_base}/__test__/reset",
        headers={"Host": status_host},
    )
    assert response.status_code == 404
    assert "unknown_path" in response.text


def test_test_control_still_available_direct_to_upstream(
    upstream_http: httpx.Client, upstream_api_base: str, require_stack: None
) -> None:
    response = upstream_http.get(f"{upstream_api_base}/__test__/state")
    assert response.status_code == 200
    assert "state" in response.json()


def test_correlation_on_status_route(
    http: httpx.Client, envoy_base: str, status_host: str, require_stack: None
) -> None:
    response = http.get(
        f"{envoy_base}/api/v1/status",
        headers={"Host": status_host, "x-request-id": "status-corr-1"},
    )
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "status-corr-1"
    assert response.json()["request_id"] == "status-corr-1"


def test_upstream_failure_through_routed_https(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    for port in (9001, 9003):
        cfg = upstream_http.post(
            f"http://127.0.0.1:{port}/__test__/errors",
            json={"mode": "http_503", "count": 5},
        )
        assert cfg.status_code == 200
    response = http.get(f"{envoy_base}/api/v2/items", headers={"Host": api_host})
    assert response.status_code == 503
    assert response.json()["behavior"] == "http_503"
    assert response.json()["instance_id"] in {"api-1", "api-2"}
