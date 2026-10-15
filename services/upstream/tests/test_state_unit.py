"""Unit tests for in-process injection state accounting."""

from __future__ import annotations

from app.state import InjectionState


def test_token_error_budget_exhausts() -> None:
    state = InjectionState()
    state.set_errors("http_500", 1)
    assert state.consume_error() == "http_500"
    assert state.consume_error() == "none"
    assert state.snapshot()["error_mode"] == "none"


def test_reset_clears_all() -> None:
    state = InjectionState()
    state.set_latency(10)
    state.set_errors("http_503", None)
    state.set_healthy(False)
    state.reset()
    assert state.snapshot() == {
        "latency_ms": 0,
        "error_mode": "none",
        "error_remaining": None,
        "healthy": True,
    }
