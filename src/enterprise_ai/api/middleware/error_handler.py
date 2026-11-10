"""Global error handling middleware transforming exceptions into uniform JSON responses."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from enterprise_ai.core.exceptions import (
    AuthError,
    DatabaseError,
    DocumentNotFoundError,
    DocumentValidationError,
    ExternalProviderError,
    InsufficientPermissionsError,
    PlatformError,
    ValidationError,
)
from enterprise_ai.core.logging import get_logger
from enterprise_ai.schemas.common import ErrorDetail, ErrorResponse

logger = get_logger("enterprise_ai.error_handler")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Convert domain and unhandled errors to a safe, consistent response."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            return await call_next(request)
        except DocumentNotFoundError as exc:
            return self._error_response(request, 404, "resource_not_found", "Resource not found", exc)
        except InsufficientPermissionsError as exc:
            return self._error_response(
                request,
                403,
                "forbidden",
                "You do not have permission to access this resource",
                exc,
            )
        except AuthError as exc:
            return self._error_response(request, 401, "unauthorized", "Authentication is required", exc)
        except (DocumentValidationError, ValidationError) as exc:
            return self._error_response(request, 400, "invalid_request", "The request could not be processed", exc)
        except DatabaseError as exc:
            return self._error_response(
                request,
                503,
                "dependency_unavailable",
                "A required service is unavailable",
                exc,
            )
        except ExternalProviderError as exc:
            return self._error_response(
                request,
                502,
                "provider_error",
                "An external provider request failed",
                exc,
            )
        except PlatformError as exc:
            return self._error_response(request, 500, "application_error", "An application error occurred", exc)
        except Exception as exc:
            return self._error_response(
                request,
                500,
                "internal_error",
                "An internal server error occurred",
                exc,
            )

    @staticmethod
    def _error_response(
        request: Request,
        status_code: int,
        code: str,
        message: str,
        exception: Exception,
    ) -> JSONResponse:
        """Log an error category and return no exception details to the client."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error(
            "request_failed",
            request_id=request_id,
            error_code=code,
            error_type=type(exception).__name__,
        )
        body = ErrorResponse(
            error=ErrorDetail(code=code, message=message),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=status_code,
            content=body.model_dump(mode="json"),
            headers={"X-Request-ID": request_id},
        )
