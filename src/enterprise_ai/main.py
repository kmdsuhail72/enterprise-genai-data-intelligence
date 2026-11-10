"""FastAPI application factory and process lifecycle."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from enterprise_ai import __version__
from enterprise_ai.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from enterprise_ai.api.routes import api_router
from enterprise_ai.api.routes.health import router as health_router
from enterprise_ai.core.config import get_settings
from enterprise_ai.core.constants import API_V1_PREFIX
from enterprise_ai.core.logging import get_logger, setup_logging
from enterprise_ai.database.connection import dispose_engine
from enterprise_ai.schemas.common import ErrorDetail, ErrorResponse


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Configure logging on startup and dispose database resources on shutdown."""
    settings = get_settings()
    setup_logging(settings)
    logger = get_logger("enterprise_ai.main")
    logger.info("application_starting", app_name=settings.app_name, environment=settings.app_env)
    try:
        yield
    finally:
        await dispose_engine()
        logger.info("application_stopped")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Enterprise document intelligence with evidence-grounded answers and analytics.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url=f"{API_V1_PREFIX}/openapi.json" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        _: RequestValidationError,
    ) -> JSONResponse:
        """Return validation errors without echoing potentially sensitive input."""
        return _error_response(request, 422, "validation_error", "Request validation failed")

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Normalize HTTP errors without exposing arbitrary exception details."""
        if exc.status_code == 404:
            code, message = "not_found", "Resource not found"
        elif exc.status_code < 500:
            code, message = "http_error", "The request could not be processed"
        else:
            code, message = "internal_error", "An internal server error occurred"
        result = _error_response(request, exc.status_code, code, message)
        if exc.headers:
            result.headers.update(exc.headers)
        return result

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        """Return non-sensitive service metadata."""
        return {"app": settings.app_name, "version": __version__, "status": "online"}

    app.include_router(health_router)
    app.include_router(api_router)
    return app


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    """Build the standard error response and carry the request correlation ID."""
    request_id = getattr(request.state, "request_id", "unavailable")
    error = ErrorResponse(
        error=ErrorDetail(code=code, message=message),
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=error.model_dump(mode="json"))


app = create_app()
