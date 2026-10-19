"""Milestone 6: active health checks, timeouts, retries, recovery."""

from __future__ import annotations

import time

import httpx
import pytest

API_INSTANCES = {"api-1", "api-2"}
ENVOY_ADMIN = "http://127.0.0.1:9901"


def _collect_instances(
    http: httpx.Client, envoy_base: str, api_host: str, n: int = 20
) -> set[str]:
    seen: set[str] = set()
    for _ in range(n):
        response = http.get(f"{envoy_base}/api/v1/items", headers={"Host": api_host})
        assert response.status_code == 200, response.text
        seen.add(response.json()["instance_id"])
    return seen


def _wait_for_only_instance(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    expected: str,
    timeout_s: float = 30.0,
) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        seen = _collect_instances(http, envoy_base, api_host, n=12)
        if seen == {expected}:
            return
        time.sleep(0.5)
    raise AssertionError(
        f"expected only {expected}, last seen {_collect_instances(http, envoy_base, api_host, n=8)}"
    )


def test_healthy_upstream_serves_both_api_instances(
    http: httpx.Client, envoy_base: str, api_host: str, require_stack: None
) -> None:
    seen = _collect_instances(http, envoy_base, api_host, n=30)
    assert seen == API_INSTANCES, seen


def test_active_health_check_removes_unhealthy_upstream(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    # Control path: mark api-2 intentionally unhealthy (/health → 503).
    # Data-path 5xx injection would NOT remove the host — HC uses /health.
    bad = upstream_http.post(
        "http://127.0.0.1:9003/__test__/health",
        json={"healthy": False},
    )
    assert bad.status_code == 200

    _wait_for_only_instance(http, envoy_base, api_host, "api-1")

    # Admin view should show at least one unhealthy upstream_api host.
    clusters = httpx.get(f"{ENVOY_ADMIN}/clusters", timeout=5.0).text
    assert "upstream_api" in clusters
    assert (
        "health_flags::/failed_active_hc" in clusters or "failed_active_hc" in clusters
    )


def test_upstream_recovery_after_health_restored(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    upstream_http.post(
        "http://127.0.0.1:9003/__test__/health",
        json={"healthy": False},
    )
    _wait_for_only_instance(http, envoy_base, api_host, "api-1")

    ok = upstream_http.post(
        "http://127.0.0.1:9003/__test__/health",
        json={"healthy": True},
    )
    assert ok.status_code == 200

    deadline = time.time() + 30
    while time.time() < deadline:
        seen = _collect_instances(http, envoy_base, api_host, n=20)
        if seen == API_INSTANCES:
            return
        time.sleep(0.5)
    raise AssertionError("api-2 did not return to the pool after recovery")


def test_slow_upstream_hits_request_timeout(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    # Both instances delayed beyond route timeout (3s) / per-try (1s).
    for port in (9001, 9003):
        cfg = upstream_http.post(
            f"http://127.0.0.1:{port}/__test__/latency",
            json={"delay_ms": 5000},
        )
        assert cfg.status_code == 200

    response = http.get(
        f"{envoy_base}/api/v1/items",
        headers={"Host": api_host, "x-request-id": "timeout-corr"},
        timeout=10.0,
    )
    assert response.status_code in {504, 503, 500}
    assert response.headers.get("x-request-id") == "timeout-corr"


def test_injected_5xx_is_visible_and_not_retried_as_http_error(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    """HTTP 5xx is application failure — not in retry_on — so attempt count stays 1."""
    for port in (9001, 9003):
        upstream_http.post(
            f"http://127.0.0.1:{port}/__test__/errors",
            json={"mode": "http_500", "count": 20},
        )

    response = http.get(
        f"{envoy_base}/api/v1/items",
        headers={"Host": api_host, "x-request-id": "no-retry-5xx"},
    )
    assert response.status_code == 500
    assert response.json()["behavior"] == "http_500"
    assert response.headers.get("x-request-id") == "no-retry-5xx"
    attempt = response.headers.get("x-envoy-attempt-count", "1")
    assert attempt == "1"


def test_data_plane_5xx_does_not_alone_remove_host_from_pool(
    http: httpx.Client,
    upstream_http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    """Ordinary request 5xx ≠ active HC failure ( /health still 200 )."""
    upstream_http.post(
        "http://127.0.0.1:9003/__test__/errors",
        json={"mode": "http_500", "count": 5},
    )
    # Give HC several intervals; data-path 5xx must not flip active HC.
    time.sleep(5)
    health = upstream_http.get("http://127.0.0.1:9003/health")
    assert health.status_code == 200
    clusters = httpx.get(f"{ENVOY_ADMIN}/clusters", timeout=5.0).text
    # Both members remain actively healthy (no failed_active_hc on api cluster).
    api_health_lines = [
        line
        for line in clusters.splitlines()
        if "upstream_api::" in line and "health_flags" in line
    ]
    assert api_health_lines, clusters
    assert all(
        "healthy" in line and "failed_active_hc" not in line
        for line in api_health_lines
    )

    # Drain remaining injected errors, then both instances must still serve.
    for _ in range(20):
        http.get(f"{envoy_base}/api/v1/items", headers={"Host": api_host})
    upstream_http.post("http://127.0.0.1:9003/__test__/reset")
    time.sleep(1)
    seen = _collect_instances(http, envoy_base, api_host, n=30)
    assert seen == API_INSTANCES, seen


def _compose(*args: str) -> None:
    import subprocess

    result = subprocess.run(
        ["docker", "compose", *args],
        capture_output=True,
        text=True,
        cwd=".",
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _wait_stack_healthy(
    http: httpx.Client, envoy_base: str, api_host: str, timeout_s: float = 60.0
) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            response = http.get(
                f"{envoy_base}/health", headers={"Host": api_host}, timeout=2.0
            )
            if response.status_code == 200:
                seen = _collect_instances(http, envoy_base, api_host, n=20)
                if seen == API_INSTANCES:
                    return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    pytest.fail("api cluster did not recover after restart")


@pytest.mark.slow
def test_stopped_upstream_removed_then_recovers(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    _compose("stop", "upstream-api-2")
    try:
        _wait_for_only_instance(http, envoy_base, api_host, "api-1", timeout_s=40.0)
        clusters = httpx.get(f"{ENVOY_ADMIN}/clusters", timeout=5.0).text
        assert "failed_active_hc" in clusters
    finally:
        _compose("start", "upstream-api-2")
        _wait_stack_healthy(http, envoy_base, api_host)


@pytest.mark.slow
def test_eligible_retry_succeeds_when_one_peer_down(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    """Connect-failure to a stopped peer may retry onto the healthy peer."""
    _compose("stop", "upstream-api-2")
    try:
        # Before HC fully removes api-2, retries should still yield 200 from api-1.
        deadline = time.time() + 15
        saw_success = False
        while time.time() < deadline:
            response = http.get(
                f"{envoy_base}/api/v1/items",
                headers={"Host": api_host, "x-request-id": "retry-ok"},
                timeout=5.0,
            )
            if response.status_code == 200:
                assert response.json()["instance_id"] == "api-1"
                assert response.headers.get("x-request-id") == "retry-ok"
                saw_success = True
                break
            time.sleep(0.2)
        assert saw_success, "expected retry onto healthy api-1"
    finally:
        _compose("start", "upstream-api-2")
        _wait_stack_healthy(http, envoy_base, api_host)


@pytest.mark.slow
def test_retry_exhaustion_and_correlation_on_connection_failure(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    _compose("stop", "upstream-api", "upstream-api-2")
    try:
        deadline = time.time() + 25
        last = None
        while time.time() < deadline:
            response = http.get(
                f"{envoy_base}/api/v1/items",
                headers={"Host": api_host, "x-request-id": "retry-exhausted"},
                timeout=5.0,
            )
            last = response.status_code
            if response.status_code >= 500:
                assert response.headers.get("x-request-id") == "retry-exhausted"
                # 1 original + up to 2 retries → attempt count may be 2 or 3
                # depending on HC state / host selection.
                attempt = int(response.headers.get("x-envoy-attempt-count", "1"))
                assert attempt >= 1
                assert attempt <= 3
                return
            time.sleep(0.5)
        raise AssertionError(f"expected upstream failure, last={last}")
    finally:
        _compose("start", "upstream-api", "upstream-api-2")
        _wait_stack_healthy(http, envoy_base, api_host)


@pytest.mark.slow
def test_connection_failure_when_both_api_instances_stopped(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    _compose("stop", "upstream-api", "upstream-api-2")
    try:
        deadline = time.time() + 25
        last = None
        while time.time() < deadline:
            response = http.get(
                f"{envoy_base}/api/v1/items",
                headers={"Host": api_host, "x-request-id": "conn-fail"},
                timeout=5.0,
            )
            last = response.status_code
            if response.status_code >= 500:
                assert response.headers.get("x-request-id") == "conn-fail"
                return
            time.sleep(0.5)
        raise AssertionError(f"expected upstream failure, last={last}")
    finally:
        _compose("start", "upstream-api", "upstream-api-2")
        _wait_stack_healthy(http, envoy_base, api_host)
