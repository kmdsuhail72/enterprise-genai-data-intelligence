"""Application liveness and dependency-readiness endpoints."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from enterprise_ai import __version__
from enterprise_ai.api.dependencies import get_app_settings
from enterprise_ai.core.config import Settings
from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.connection import get_engine
from enterprise_ai.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
logger = get_logger("enterprise_ai.health")


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    """Report that the API process is alive without probing external services."""
    return HealthResponse(application=settings.app_name, version=__version__)


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_probe(
    response: Response,
    settings: Settings = Depends(get_app_settings),
) -> ReadinessResponse:
    """Probe the database dependency and return 503 when it is unavailable."""
    database_available = await _database_is_available()
    if not database_available:
        checks = {"database": "unavailable"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        probe_status = "not_ready"
    else:
        checks = {"database": "connected"}
        probe_status = "ready"

    return ReadinessResponse(
        status=probe_status,
        application=settings.app_name,
        version=__version__,
        checks=checks,
    )


async def _database_is_available() -> bool:
    """Run a bounded database-free query and suppress infrastructure details."""
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as exc:
        logger.warning("readiness_check_failed", dependency="database", error_type=type(exc).__name__)
        return False
    return True
