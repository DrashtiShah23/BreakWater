"""Failure path: Envoy behavior when an upstream member is unreachable."""

from __future__ import annotations

import subprocess
import time

import httpx
import pytest


def _compose(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=".",
    )


@pytest.mark.slow
def test_single_api_stop_still_served_by_peer(
    http: httpx.Client,
    envoy_base: str,
    api_host: str,
    require_stack: None,
) -> None:
    """
    With two upstream_api members, stopping api-1 alone must not take the
    cluster offline — traffic continues on api-2 after HC isolation.
    """
    stop = _compose("stop", "upstream-api")
    if stop.returncode != 0:
        pytest.skip(f"could not stop upstream-api: {stop.stderr}")

    try:
        deadline = time.time() + 40
        saw_api_2 = False
        while time.time() < deadline:
            response = http.get(
                f"{envoy_base}/api/v1/items",
                headers={"Host": api_host, "x-request-id": "peer-failover"},
                timeout=5.0,
            )
            if response.status_code == 200:
                assert response.json()["instance_id"] == "api-2"
                assert response.headers.get("x-request-id") == "peer-failover"
                saw_api_2 = True
                break
            time.sleep(0.5)
        assert saw_api_2, "expected api-2 to keep serving after api-1 stop"
    finally:
        start = _compose("start", "upstream-api")
        assert start.returncode == 0, start.stderr

    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            response = http.get(
                f"{envoy_base}/health",
                headers={"Host": api_host},
                timeout=2.0,
            )
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    pytest.fail("upstream-api did not recover behind Envoy after restart")
