"""Runtime configuration for upstream surfaces."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Surface = Literal["api", "status"]


class Settings(BaseSettings):
    """Environment-driven settings. Safe defaults favor local development."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    surface: Surface = Field(default="api", validation_alias="SURFACE")
    instance_id: str = Field(default="upstream-1", validation_alias="UPSTREAM_INSTANCE_ID")
    enable_test_controls: bool = Field(default=False, validation_alias="ENABLE_TEST_CONTROLS")
    # Hard caps so test controls cannot become an accidental DoS knob.
    max_latency_ms: int = Field(default=30_000, validation_alias="MAX_LATENCY_MS")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    correlation_header: str = Field(
        default="x-request-id",
        validation_alias="CORRELATION_HEADER",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
