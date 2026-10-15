"""Request middleware: correlation IDs and allowlisted failure injection."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import Settings
from app.state import test_state

logger = logging.getLogger("breakwater.upstream")

# Never inject into test-control or docs.
_SKIP_ALL_INJECTION_PREFIXES = ("/__test__", "/docs", "/openapi.json", "/redoc")
# Liveness must stay up while the process is alive.
_SKIP_ALL_INJECTION_EXACT = {"/live"}
# Readiness should reflect intentional unhealthy only — not injected 5xx mode.
_SKIP_ERROR_INJECTION_EXACT = {"/live", "/health"}


class InjectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        started = time.perf_counter()
        header_name = self.settings.correlation_header
        request_id = request.headers.get(header_name) or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.instance_id = self.settings.instance_id
        request.state.surface = self.settings.surface

        path = request.url.path
        skip_all = path in _SKIP_ALL_INJECTION_EXACT or path.startswith(
            _SKIP_ALL_INJECTION_PREFIXES
        )
        skip_errors = skip_all or path in _SKIP_ERROR_INJECTION_EXACT

        applied_latency_ms = 0
        behavior = "normal"

        if not skip_all:
            delay = test_state.current_latency_ms()
            if delay > 0:
                await asyncio.sleep(delay / 1000.0)
                applied_latency_ms = delay
                behavior = "latency"

            if not skip_errors:
                error_mode = test_state.consume_error()
                if error_mode == "http_500":
                    behavior = "http_500"
                    return self._error_response(
                        request, request_id, 500, behavior, applied_latency_ms
                    )
                if error_mode == "http_503":
                    behavior = "http_503"
                    return self._error_response(
                        request, request_id, 503, behavior, applied_latency_ms
                    )

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)

        response.headers[header_name] = request_id
        response.headers["x-upstream-instance"] = self.settings.instance_id
        response.headers["x-upstream-surface"] = self.settings.surface
        response.headers["x-upstream-behavior"] = behavior
        if applied_latency_ms:
            response.headers["x-upstream-injected-latency-ms"] = str(applied_latency_ms)

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "instance_id": self.settings.instance_id,
                "surface": self.settings.surface,
                "path": path,
                "method": request.method,
                "status_code": response.status_code,
                "latency_ms": elapsed_ms,
                "behavior": behavior,
            },
        )
        return response

    def _error_response(
        self,
        request: Request,
        request_id: str,
        status_code: int,
        behavior: str,
        applied_latency_ms: int,
    ) -> JSONResponse:
        body = {
            "error": "injected_upstream_error",
            "behavior": behavior,
            "instance_id": self.settings.instance_id,
            "surface": self.settings.surface,
            "request_id": request_id,
            "path": request.url.path,
        }
        headers = {
            self.settings.correlation_header: request_id,
            "x-upstream-instance": self.settings.instance_id,
            "x-upstream-surface": self.settings.surface,
            "x-upstream-behavior": behavior,
        }
        if applied_latency_ms:
            headers["x-upstream-injected-latency-ms"] = str(applied_latency_ms)
        logger.info(
            "injected error response",
            extra={
                "request_id": request_id,
                "instance_id": self.settings.instance_id,
                "surface": self.settings.surface,
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "behavior": behavior,
            },
        )
        return JSONResponse(status_code=status_code, content=body, headers=headers)
