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


class PageParams(BaseModel):
    """Reusable request parameters for paginated reads."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized pagination response."""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 25
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False


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
