"""Pydantic schemas for analytics and metrics reporting."""

from typing import Any

from pydantic import BaseModel, Field


class AnalyticsSummaryResponse(BaseModel):
    """Schema for platform analytics summary."""
    total_documents: int
    total_chunks: int
    system_status: str
    metadata: dict[str, Any] = Field(default_factory=dict)

