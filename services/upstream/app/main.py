"""Application factory for api and status upstream surfaces."""

from __future__ import annotations

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.middleware import InjectionMiddleware
from app.routes import health, items, status_surface
from app.routes.test_control import build_test_control_router
from app.state import test_state


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    # Fresh state per app instance (important for tests).
    test_state.reset()

    app = FastAPI(
        title=f"Breakwater upstream ({settings.surface})",
        version="0.1.0",
        docs_url="/docs" if settings.enable_test_controls else None,
        redoc_url=None,
    )
    app.state.settings = settings

    app.add_middleware(InjectionMiddleware, settings=settings)
    app.include_router(health.router)

    if settings.surface == "api":
        app.include_router(items.router)
    elif settings.surface == "status":
        app.include_router(status_surface.router)
    else:
        raise ValueError(f"unsupported SURFACE: {settings.surface}")

    if settings.enable_test_controls:
        app.include_router(build_test_control_router(settings))

    @app.get("/")
    async def root() -> dict[str, object]:
        return {
            "service": "breakwater-upstream",
            "surface": settings.surface,
            "instance_id": settings.instance_id,
            "test_controls": settings.enable_test_controls,
        }

    return app


# Default ASGI app for `uvicorn app.main:app` (SURFACE from environment).
app = create_app()
