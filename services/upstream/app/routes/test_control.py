"""Allowlisted development/test failure-injection controls.

Mounted only when ENABLE_TEST_CONTROLS=true. Absent (404) otherwise —
the AWS validation path should disable this flag.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.config import Settings
from app.state import ErrorMode, test_state

logger = logging.getLogger("breakwater.upstream.test_control")


class LatencyRequest(BaseModel):
    delay_ms: int = Field(
        ...,
        ge=0,
        description="Artificial delay applied to subsequent data requests",
    )


class ErrorsRequest(BaseModel):
    mode: ErrorMode
    # None => until reset; integer => that many injected errors then auto-clear.
    count: int | None = Field(
        default=None,
        description="Number of injected errors; omit for until reset",
    )

    @field_validator("count")
    @classmethod
    def count_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("count must be >= 0")
        return value


class HealthRequest(BaseModel):
    healthy: bool


class CrashRequest(BaseModel):
    """Acknowledge a deliberate process exit. No arbitrary commands."""

    confirm: Literal[True]


def build_test_control_router(settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/__test__", tags=["test-control"])
    max_latency = settings.max_latency_ms

    @router.get("/state")
    async def get_state(request: Request) -> dict[str, object]:
        return {
            "instance_id": settings.instance_id,
            "surface": settings.surface,
            "request_id": request.state.request_id,
            "state": test_state.snapshot(),
            "limits": {"max_latency_ms": max_latency},
        }

    @router.post("/latency")
    async def set_latency(body: LatencyRequest, request: Request) -> dict[str, object]:
        if body.delay_ms > max_latency:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_test_control",
                    "message": f"delay_ms exceeds max_latency_ms ({max_latency})",
                    "request_id": request.state.request_id,
                },
            )
        test_state.set_latency(body.delay_ms)
        logger.info(
            "latency configured",
            extra={
                "request_id": request.state.request_id,
                "instance_id": settings.instance_id,
                "surface": settings.surface,
                "behavior": f"latency={body.delay_ms}",
            },
        )
        return {
            "ok": True,
            "latency_ms": body.delay_ms,
            "instance_id": settings.instance_id,
            "request_id": request.state.request_id,
        }

    @router.post("/errors")
    async def set_errors(body: ErrorsRequest, request: Request) -> dict[str, object]:
        if body.mode == "none":
            test_state.set_errors("none", None)
        else:
            test_state.set_errors(body.mode, body.count)
        return {
            "ok": True,
            "error_mode": body.mode,
            "error_remaining": body.count if body.mode != "none" else None,
            "instance_id": settings.instance_id,
            "request_id": request.state.request_id,
        }

    @router.post("/health")
    async def set_health(body: HealthRequest, request: Request) -> dict[str, object]:
        test_state.set_healthy(body.healthy)
        return {
            "ok": True,
            "healthy": body.healthy,
            "instance_id": settings.instance_id,
            "request_id": request.state.request_id,
        }

    @router.post("/reset")
    async def reset(request: Request) -> dict[str, object]:
        test_state.reset()
        return {
            "ok": True,
            "state": test_state.snapshot(),
            "instance_id": settings.instance_id,
            "request_id": request.state.request_id,
        }

    @router.post("/crash")
    async def crash(body: CrashRequest, request: Request) -> dict[str, object]:
        # Respond first; exit shortly after so clients observe an ACK then death.
        async def _exit_soon() -> None:
            await asyncio.sleep(0.05)
            logger.warning(
                "intentional process crash",
                extra={
                    "request_id": request.state.request_id,
                    "instance_id": settings.instance_id,
                    "surface": settings.surface,
                    "behavior": "crash",
                },
            )
            os._exit(1)

        asyncio.create_task(_exit_soon())
        return {
            "ok": True,
            "action": "crash_scheduled",
            "instance_id": settings.instance_id,
            "request_id": request.state.request_id,
        }

    return router
