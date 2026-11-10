"""Dependency injection helpers for FastAPI endpoints."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.config import Settings, get_settings
from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.connection import async_session_factory

logger = get_logger(__name__)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session.

    The session is committed automatically when the request handler returns
    without error. On exception the transaction is rolled back.
    """
    session = await async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_config() -> Settings:
    """Provide application settings (cached singleton)."""
    return get_settings()
