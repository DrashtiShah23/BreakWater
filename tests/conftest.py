"""Root pytest configuration hooks."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "slow: exercises container stop/start failure paths")
