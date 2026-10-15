"""Failure path: Envoy behavior when the upstream data-plane target is unreachable."""

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
def test_envoy_returns_upstream_failure_when_api_stopped(
    http: httpx.Client,
    envoy_base: str,
    require_stack: None,
) -> None:
    """
    Stop upstream-api briefly and assert the edge surfaces an upstream failure.
    Restores the service afterward so later tests are not poisoned.
    """
    stop = _compose("stop", "upstream-api")
    if stop.returncode != 0:
        pytest.skip(f"could not stop upstream-api: {stop.stderr}")

    try:
        # Allow Envoy to observe the disconnect; STRICT_DNS may keep stale address briefly.
        deadline = time.time() + 20
        last_status = None
        while time.time() < deadline:
            response = http.get(f"{envoy_base}/api/v1/items", timeout=5.0)
            last_status = response.status_code
            # 503 UF/UH style failures or 5xx from Envoy when upstream is down.
            if response.status_code >= 500:
                break
            time.sleep(0.5)
        assert last_status is not None and last_status >= 500, last_status
    finally:
        start = _compose("start", "upstream-api")
        assert start.returncode == 0, start.stderr

    # Wait until data path recovers (outside finally so recovery failure is visible).
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            response = http.get(f"{envoy_base}/health", timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    pytest.fail("upstream-api did not recover behind Envoy after restart")
