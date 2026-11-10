"""Administrative endpoints for platform configuration and health monitoring."""

from fastapi import APIRouter

from enterprise_ai.core.config import get_settings
from enterprise_ai.schemas.common import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/config", response_model=APIResponse[dict])
async def get_system_config() -> APIResponse[dict]:
    """Retrieve sanitized non-sensitive runtime configuration."""
    settings = get_settings()
    return APIResponse(
        success=True,
        data={
            "app_name": settings.app_name,
            "app_env": settings.app_env,
            "db_host": settings.db_host,
            "db_port": settings.db_port,
            "embedding_provider": settings.embedding_provider,
            "llm_provider": settings.llm_provider,
        },
    )

