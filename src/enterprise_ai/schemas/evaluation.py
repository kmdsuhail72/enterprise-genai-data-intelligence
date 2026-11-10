"""Pydantic schemas for RAG evaluation benchmarks."""

from pydantic import BaseModel, Field


class EvaluationBenchmarkResponse(BaseModel):
    """Schema for RAG evaluation metrics."""
    recall_at_k: float = Field(..., ge=0.0, le=1.0)
    precision_at_k: float = Field(..., ge=0.0, le=1.0)
    mrr: float = Field(..., ge=0.0, le=1.0)
    ndcg: float = Field(..., ge=0.0, le=1.0)
    faithfulness_score: float = Field(..., ge=0.0, le=1.0)
    citation_precision: float = Field(..., ge=0.0, le=1.0)

