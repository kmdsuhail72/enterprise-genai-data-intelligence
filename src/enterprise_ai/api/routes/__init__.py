"""API route registration aggregating sub-routers."""

from fastapi import APIRouter

from enterprise_ai.api.routes.admin import router as admin_router
from enterprise_ai.api.routes.analytics import router as analytics_router
from enterprise_ai.api.routes.chat import router as chat_router
from enterprise_ai.api.routes.documents import router as documents_router
from enterprise_ai.api.routes.health import router as health_router
from enterprise_ai.core.constants import API_V1_PREFIX

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(analytics_router)
api_router.include_router(admin_router)
