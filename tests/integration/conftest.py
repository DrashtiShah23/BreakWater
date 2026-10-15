"""Fixtures for Compose-backed edge integration tests (Milestone 3+)."""

from __future__ import annotations

import os
import time

import httpx
import pytest

ENVOY_BASE = os.environ.get("BREAKWATER_ENVOY_URL", "http://127.0.0.1:8080").rstrip("/")
UPSTREAM_API_BASE = os.environ.get(
    "BREAKWATER_UPSTREAM_API_URL", "http://127.0.0.1:9001"
).rstrip("/")
ENVOY_ADMIN = os.environ.get(
    "BREAKWATER_ENVOY_ADMIN_URL", "http://127.0.0.1:9901"
).rstrip("/")


def _wait_http(url: str, timeout_s: float = 60.0) -> None:
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code < 500:
                return
        except Exception as exc:  # noqa: BLE001 - poll until ready
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


@pytest.fixture(scope="session")
def envoy_base() -> str:
    return ENVOY_BASE


@pytest.fixture(scope="session")
def upstream_api_base() -> str:
    return UPSTREAM_API_BASE


@pytest.fixture(scope="session")
def require_stack(envoy_base: str, upstream_api_base: str) -> None:
    """Skip the session if the local Compose edge stack is not running."""
    if os.environ.get("BREAKWATER_SKIP_INTEGRATION") == "1":
        pytest.skip("BREAKWATER_SKIP_INTEGRATION=1")
    try:
        _wait_http(f"{upstream_api_base}/health", timeout_s=5.0)
        _wait_http(f"{envoy_base}/health", timeout_s=5.0)
        _wait_http(f"{ENVOY_ADMIN}/ready", timeout_s=5.0)
    except RuntimeError as exc:
        pytest.skip(f"edge stack not reachable (run `make up` first): {exc}")


@pytest.fixture
def http() -> httpx.Client:
    with httpx.Client(timeout=30.0) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_upstream_injection(
    http: httpx.Client, upstream_api_base: str, require_stack: None
) -> None:
    http.post(f"{upstream_api_base}/__test__/reset")
    yield
    http.post(f"{upstream_api_base}/__test__/reset")
