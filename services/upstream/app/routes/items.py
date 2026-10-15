"""Versioned items API — primary data-plane sample surface."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["items"])

_V1_ITEMS = [
    {"id": "item-1", "name": "anchor", "version": "v1"},
    {"id": "item-2", "name": "bollard", "version": "v1"},
]

_V2_ITEMS = [
    {"id": "item-1", "name": "anchor", "sku": "ANC-001", "version": "v2"},
    {"id": "item-2", "name": "bollard", "sku": "BOL-002", "version": "v2"},
    {"id": "item-3", "name": "cleat", "sku": "CLE-003", "version": "v2"},
]


def _envelope(request: Request, api_version: str, items: list[dict]) -> dict[str, object]:
    return {
        "api_version": api_version,
        "instance_id": request.state.instance_id,
        "surface": request.state.surface,
        "request_id": request.state.request_id,
        "behavior": "normal",
        "items": items,
        "count": len(items),
    }


@router.get("/api/v1/items")
async def list_items_v1(request: Request) -> dict[str, object]:
    return _envelope(request, "v1", _V1_ITEMS)


@router.get("/api/v2/items")
async def list_items_v2(request: Request) -> dict[str, object]:
    return _envelope(request, "v2", _V2_ITEMS)
