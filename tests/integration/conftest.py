"""Fixtures for Compose-backed edge integration tests (Milestone 3+)."""

from __future__ import annotations

import os
import ssl
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CA = REPO_ROOT / "envoy" / "tls" / "ca.crt"

ENVOY_BASE = os.environ.get("BREAKWATER_ENVOY_URL", "https://127.0.0.1:8443").rstrip(
    "/"
)
UPSTREAM_API_BASE = os.environ.get(
    "BREAKWATER_UPSTREAM_API_URL", "http://127.0.0.1:9001"
).rstrip("/")
UPSTREAM_STATUS_BASE = os.environ.get(
    "BREAKWATER_UPSTREAM_STATUS_URL", "http://127.0.0.1:9002"
).rstrip("/")
ENVOY_ADMIN = os.environ.get(
    "BREAKWATER_ENVOY_ADMIN_URL", "http://127.0.0.1:9901"
).rstrip("/")
CA_CERT_PATH = Path(os.environ.get("BREAKWATER_CA_CERT", str(DEFAULT_CA)))

API_HOST = "api.breakwater.local"
STATUS_HOST = "status.breakwater.local"


def _ssl_context_for_ca(ca_path: Path) -> ssl.SSLContext:
    return ssl.create_default_context(cafile=str(ca_path))


def _client_kwargs() -> dict:
    kwargs: dict = {"timeout": 30.0}
    if ENVOY_BASE.startswith("https://"):
        if not CA_CERT_PATH.is_file():
            pytest.skip(
                f"missing development CA cert at {CA_CERT_PATH} (run make certs)"
            )
        kwargs["verify"] = _ssl_context_for_ca(CA_CERT_PATH)
    return kwargs


def _wait_url(
    url: str,
    *,
    verify: bool | ssl.SSLContext = True,
    headers: dict[str, str] | None = None,
    timeout_s: float = 60.0,
) -> None:
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=2.0, verify=verify, headers=headers)
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
def upstream_status_base() -> str:
    return UPSTREAM_STATUS_BASE


@pytest.fixture(scope="session")
def ca_cert_path() -> Path:
    return CA_CERT_PATH


@pytest.fixture(scope="session")
def api_host() -> str:
    return API_HOST


@pytest.fixture(scope="session")
def status_host() -> str:
    return STATUS_HOST


@pytest.fixture(scope="session")
def require_stack(
    envoy_base: str,
    upstream_api_base: str,
    ca_cert_path: Path,
    api_host: str,
) -> None:
    """Skip the session if the local Compose edge stack is not running."""
    if os.environ.get("BREAKWATER_SKIP_INTEGRATION") == "1":
        pytest.skip("BREAKWATER_SKIP_INTEGRATION=1")
    verify: bool | ssl.SSLContext = True
    if envoy_base.startswith("https://"):
        if not ca_cert_path.is_file():
            pytest.skip(
                f"missing development CA cert at {ca_cert_path} (run make certs)"
            )
        verify = _ssl_context_for_ca(ca_cert_path)
    try:
        _wait_url(f"{upstream_api_base}/health", verify=True, timeout_s=5.0)
        _wait_url(
            f"{envoy_base}/health",
            verify=verify,
            headers={"Host": api_host},
            timeout_s=5.0,
        )
        _wait_url(f"{ENVOY_ADMIN}/ready", verify=True, timeout_s=5.0)
    except RuntimeError as exc:
        pytest.skip(
            f"edge stack not reachable (run `make certs && make up` first): {exc}"
        )


@pytest.fixture
def http() -> httpx.Client:
    with httpx.Client(**_client_kwargs()) as client:
        yield client


@pytest.fixture
def upstream_http() -> httpx.Client:
    """Plain HTTP client for direct upstream / test-control calls."""
    with httpx.Client(timeout=30.0) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_upstream_injection(
    upstream_http: httpx.Client,
    upstream_api_base: str,
    upstream_status_base: str,
    require_stack: None,
) -> None:
    upstream_http.post(f"{upstream_api_base}/__test__/reset")
    upstream_http.post(f"{upstream_status_base}/__test__/reset")
    yield
    upstream_http.post(f"{upstream_api_base}/__test__/reset")
    upstream_http.post(f"{upstream_status_base}/__test__/reset")
