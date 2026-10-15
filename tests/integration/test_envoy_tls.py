"""Milestone 4: TLS terminates at Envoy; upstream remains HTTP."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest


def test_https_health_through_envoy(
    http: httpx.Client, envoy_base: str, require_stack: None
) -> None:
    assert envoy_base.startswith("https://")
    response = http.get(f"{envoy_base}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] is True
    assert body["instance_id"] == "api-1"
    assert response.headers.get("x-upstream-instance") == "api-1"


def test_https_items_through_envoy(
    http: httpx.Client, envoy_base: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/api/v1/items")
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["instance_id"] == "api-1"
    assert response.headers.get("x-upstream-surface") == "api"


def test_https_correlation_id_preserved(
    http: httpx.Client, envoy_base: str, require_stack: None
) -> None:
    response = http.get(
        f"{envoy_base}/api/v1/items",
        headers={"x-request-id": "tls-corr-m4"},
    )
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "tls-corr-m4"
    assert response.json()["request_id"] == "tls-corr-m4"


def test_https_unknown_path_404(
    http: httpx.Client, envoy_base: str, require_stack: None
) -> None:
    response = http.get(f"{envoy_base}/does-not-exist")
    assert response.status_code == 404
    assert "unknown_path" in response.text


def test_https_injected_5xx_passes_through(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    upstream_api_base: str,
    require_stack: None,
) -> None:
    cfg = upstream_http.post(
        f"{upstream_api_base}/__test__/errors",
        json={"mode": "http_500", "count": 1},
    )
    assert cfg.status_code == 200
    response = http.get(f"{envoy_base}/api/v1/items")
    assert response.status_code == 500
    assert response.json()["behavior"] == "http_500"


def test_untrusted_certificate_rejected(envoy_base: str, require_stack: None) -> None:
    """System trust store does not include the local Dev CA — handshake must fail."""
    assert envoy_base.startswith("https://")
    with pytest.raises(httpx.ConnectError):
        httpx.get(f"{envoy_base}/health", timeout=5.0, verify=True)


def test_ca_cert_file_is_local_and_not_required_in_git(
    ca_cert_path: Path, require_stack: None
) -> None:
    assert ca_cert_path.is_file()
    assert ca_cert_path.name == "ca.crt"
    # Private keys must exist locally for Envoy but remain gitignored.
    key = ca_cert_path.parent / "server.key"
    assert key.is_file()
