"""Deliberately small status host surface (not an admin product)."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["status"])


@router.get("/api/v1/status")
async def status_v1(request: Request) -> dict[str, object]:
    return {
        "api_version": "v1",
        "service": "status",
        "message": "ok",
        "instance_id": request.state.instance_id,
        "surface": request.state.surface,
        "request_id": request.state.request_id,
        "behavior": "normal",
    }
