"""Authentication and token extraction middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from enterprise_ai.core.security import decode_access_token


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Parses Authorization bearer token and attaches principal claims to request state."""

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode_access_token(token)
                request.state.user = payload
            except Exception:
                # Malformed/expired token attached to state for route handlers to inspect
                request.state.user = None
        else:
            request.state.user = None

        return await call_next(request)

