"""Structured JSON logging for application events."""

import logging
import sys
from typing import Any

import structlog

from enterprise_ai.core.config import Settings, get_settings


def setup_logging(settings: Settings | None = None) -> None:
    """Configure stdlib and structlog loggers with a consistent JSON format."""
    app_settings = settings or get_settings()
    log_level = getattr(logging, app_settings.app_log_level)
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.basicConfig(level=log_level, handlers=[handler], force=True)


def get_logger(name: str | None = None) -> Any:
    """Return a structured logger bound to an optional module name."""
    return structlog.get_logger(name)
