"""Response contracts for health and readiness probes."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness response that does not depend on external services."""

    status: Literal["healthy"] = "healthy"
    application: str
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReadinessResponse(BaseModel):
    """Readiness response with the state of critical dependencies."""

    status: Literal["ready", "not_ready"]
    application: str
    version: str
    checks: dict[str, Literal["connected", "unavailable"]]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
