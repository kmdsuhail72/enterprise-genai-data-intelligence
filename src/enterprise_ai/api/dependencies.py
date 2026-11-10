"""FastAPI route dependencies providing database sessions and application services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.config import Settings, get_settings
from enterprise_ai.core.dependencies import get_db_session
from enterprise_ai.services.analytics_service import AnalyticsService
from enterprise_ai.services.chat_service import ChatService
from enterprise_ai.services.document_service import DocumentService
from enterprise_ai.services.user_service import UserService


def get_app_settings() -> Settings:
    """Provide validated application configuration to route dependencies."""
    return get_settings()


def get_document_service(session: AsyncSession = Depends(get_db_session)) -> DocumentService:
    """Provide DocumentService instance."""
    return DocumentService(session=session)


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    """Provide ChatService instance."""
    return ChatService(session=session)


def get_analytics_service(session: AsyncSession = Depends(get_db_session)) -> AnalyticsService:
    """Provide AnalyticsService instance."""
    return AnalyticsService(session=session)


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    """Provide UserService instance."""
    return UserService(session=session)
