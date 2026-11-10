"""Shared response schemas for pagination, timestamps, and API errors."""

from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API envelope."""

    success: bool = True
    data: T | None = None
    message: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized pagination response."""

    items: list[T]
    total: int
    skip: int
    limit: int


class ErrorDetail(BaseModel):
    """Safe, machine-readable error information."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Consistent error envelope returned by the HTTP API."""

    success: bool = False
    error: ErrorDetail
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
