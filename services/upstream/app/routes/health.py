"""Liveness and readiness endpoints for later Envoy active health checks."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.state import test_state

router = APIRouter(tags=["health"])


def _meta(request: Request) -> dict[str, str]:
    return {
        "instance_id": request.state.instance_id,
        "surface": request.state.surface,
        "request_id": request.state.request_id,
    }


@router.get("/live")
async def live(request: Request) -> dict[str, object]:
    """Process-alive probe. Ignores intentional unhealthy flag."""
    return {
        "status": "alive",
        "healthy": True,
        **_meta(request),
    }


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    """Application readiness for Envoy. Honors intentional unhealthy state."""
    meta = _meta(request)
    if not test_state.is_healthy():
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "healthy": False,
                "reason": "intentional_unhealthy",
                **meta,
            },
        )
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "healthy": True,
            **meta,
        },
    )
