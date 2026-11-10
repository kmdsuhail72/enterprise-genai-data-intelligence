"""Cryptographic, password hashing, and token utilities for Enterprise GenAI Platform."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from enterprise_ai.core.config import get_settings
from enterprise_ai.core.exceptions import ConfigurationError, InvalidCredentialsError, TokenExpiredError

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a raw password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a given password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Generate signed JWT access token."""
    settings = get_settings()
    secret_key = settings.jwt_secret_key.get_secret_value()
    if not secret_key:
        raise ConfigurationError("JWT signing is not configured")
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    secret_key = settings.jwt_secret_key.get_secret_value()
    if not secret_key:
        raise ConfigurationError("JWT signing is not configured")
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired")
    except JWTError as exc:
        raise InvalidCredentialsError(f"Could not validate credentials: {exc}")


def compute_sha256(data: bytes) -> str:
    """Calculate hex-encoded SHA-256 hash of byte content."""
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()
