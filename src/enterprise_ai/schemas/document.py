"""Pydantic schemas for document ingestion and management."""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """Schema for document registration."""
    filename: str
    content_type: str
    file_size_bytes: int


class DocumentResponse(BaseModel):
    """Schema for document representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    uploaded_by: uuid.UUID
    filename: str
    content_type: str
    file_size_bytes: int
    storage_path: str
    status: str
    extraction_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

