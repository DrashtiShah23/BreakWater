"""Shared fixtures for upstream tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.state import test_state


@pytest.fixture(autouse=True)
def _reset_process_state() -> None:
    get_settings.cache_clear()
    test_state.reset()
    yield
    test_state.reset()
    get_settings.cache_clear()


@pytest.fixture
def api_settings() -> Settings:
    return Settings(
        surface="api",
        instance_id="api-test-1",
        enable_test_controls=True,
        max_latency_ms=5_000,
    )


@pytest.fixture
def status_settings() -> Settings:
    return Settings(
        surface="status",
        instance_id="status-test-1",
        enable_test_controls=True,
        max_latency_ms=5_000,
    )


@pytest.fixture
def api_client(api_settings: Settings) -> TestClient:
    return TestClient(create_app(api_settings))


@pytest.fixture
def status_client(status_settings: Settings) -> TestClient:
    return TestClient(create_app(status_settings))


@pytest.fixture
def api_client_controls_disabled() -> TestClient:
    settings = Settings(
        surface="api",
        instance_id="api-prod-like",
        enable_test_controls=False,
    )
    return TestClient(create_app(settings))
