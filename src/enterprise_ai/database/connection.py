"""Async SQLAlchemy engine and session configuration.

Uses a lazy-singleton pattern so that the engine is not created at import
time — this makes testing and configuration overrides straightforward.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the async engine, creating it on first call (lazy singleton)."""
    global _engine
    if _engine is None:
        from enterprise_ai.core.config import get_settings

        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.app_debug and not settings.is_production,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory, creating it on first call (lazy singleton)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def async_session_factory() -> AsyncSession:
    """Create and return a new :class:`AsyncSession`."""
    factory = get_session_factory()
    return factory()


async def dispose_engine() -> None:
    """Dispose of the engine and reset singletons (for graceful shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
