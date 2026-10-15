"""In-process mutable state for deterministic failure injection."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Literal

ErrorMode = Literal["none", "http_500", "http_503"]


@dataclass
class InjectionState:
    """Process-local injection state. Not shared across instances by design."""

    latency_ms: int = 0
    error_mode: ErrorMode = "none"
    # Remaining forced errors; None means until reset when error_mode != none.
    error_remaining: int | None = None
    healthy: bool = True
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "latency_ms": self.latency_ms,
                "error_mode": self.error_mode,
                "error_remaining": self.error_remaining,
                "healthy": self.healthy,
            }

    def set_latency(self, delay_ms: int) -> None:
        with self._lock:
            self.latency_ms = delay_ms

    def set_errors(self, mode: ErrorMode, remaining: int | None) -> None:
        with self._lock:
            self.error_mode = mode
            self.error_remaining = remaining if mode != "none" else None

    def set_healthy(self, healthy: bool) -> None:
        with self._lock:
            self.healthy = healthy

    def reset(self) -> None:
        with self._lock:
            self.latency_ms = 0
            self.error_mode = "none"
            self.error_remaining = None
            self.healthy = True

    def consume_error(self) -> ErrorMode:
        """Return the error mode for this request, decrementing a finite budget."""
        with self._lock:
            if self.error_mode == "none":
                return "none"
            mode = self.error_mode
            if self.error_remaining is None:
                return mode
            if self.error_remaining <= 0:
                self.error_mode = "none"
                self.error_remaining = None
                return "none"
            self.error_remaining -= 1
            if self.error_remaining <= 0:
                self.error_mode = "none"
                self.error_remaining = None
            return mode

    def is_healthy(self) -> bool:
        with self._lock:
            return self.healthy

    def current_latency_ms(self) -> int:
        with self._lock:
            return self.latency_ms


# Module-level state for the running process.
test_state = InjectionState()
