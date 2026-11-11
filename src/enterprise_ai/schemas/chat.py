"""Pydantic schemas for RAG chat and citations."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for incoming RAG question."""
    question: str = Field(..., min_length=1, description="Natural language question")
    document_ids: list[uuid.UUID] | None = Field(default=None, description="Optional document ID filters")
    llm_provider: str | None = Field(default=None, description="Requested LLM provider override")


class Citation(BaseModel):
    """Schema for verified source evidence citation."""
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page_number: int | None = None
    table_index: int | None = None
    supporting_text: str
    relevance_score: float | None = None


class ChatResponse(BaseModel):
    """Schema for RAG answer response."""
    query_id: uuid.UUID
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    latency_ms: float
    llm_provider: str
    llm_model: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

