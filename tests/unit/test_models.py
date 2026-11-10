"""Tests for database ORM models."""

import uuid
from datetime import datetime

import pytest

from enterprise_ai.database.base import (
    Base,
    User,
    UserRole,
    Document,
    DocumentStatus,
    DocumentPage,
    Chunk,
    Query,
    DocumentAccess,
    AccessPermission,
)


class TestModels:
    """Test ORM model definitions."""

    def test_user_model_has_required_columns(self):
        """Test User model has all required columns."""
        columns = {c.name for c in User.__table__.columns}
        expected = {"id", "email", "hashed_password", "full_name", "role", "is_active", "created_at", "updated_at"}
        assert expected.issubset(columns)

    def test_document_model_has_required_columns(self):
        """Test Document model has all required columns."""
        columns = {c.name for c in Document.__table__.columns}
        expected = {
            "id", "uploaded_by", "filename", "content_type",
            "file_size_bytes", "storage_path", "status",
            "extraction_metadata", "created_at", "updated_at",
        }
        assert expected.issubset(columns)

    def test_document_page_model_has_required_columns(self):
        columns = {c.name for c in DocumentPage.__table__.columns}
        expected = {
            "id", "document_id", "page_number", "raw_text",
            "cleaned_text", "extraction_method", "tables_json", "created_at",
        }
        assert expected.issubset(columns)

    def test_chunk_model_has_required_columns(self):
        columns = {c.name for c in Chunk.__table__.columns}
        expected = {
            "id", "document_id", "page_id", "chunk_index",
            "content", "content_clean", "embedding",
            "search_vector", "metadata_", "created_at",
        }
        assert expected.issubset(columns)

    def test_query_model_has_required_columns(self):
        columns = {c.name for c in Query.__table__.columns}
        expected = {
            "id", "user_id", "question", "answer", "citations",
            "retrieval_metadata", "llm_provider", "llm_model",
            "tokens_used", "cost_usd", "latency_ms", "created_at",
        }
        assert expected.issubset(columns)

    def test_document_access_model_has_required_columns(self):
        columns = {c.name for c in DocumentAccess.__table__.columns}
        expected = {"id", "document_id", "user_id", "permission", "granted_at"}
        assert expected.issubset(columns)

    def test_user_role_enum(self):
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.ANALYST.value == "analyst"
        assert UserRole.VIEWER.value == "viewer"

    def test_document_status_enum(self):
        assert DocumentStatus.PENDING.value == "pending"
        assert DocumentStatus.PROCESSING.value == "processing"
        assert DocumentStatus.COMPLETED.value == "completed"
        assert DocumentStatus.FAILED.value == "failed"

    def test_access_permission_enum(self):
        assert AccessPermission.READ.value == "read"
        assert AccessPermission.WRITE.value == "write"
        assert AccessPermission.ADMIN.value == "admin"

    def test_base_metadata(self):
        """Test that Base has metadata."""
        assert Base.metadata is not None
        table_names = set(Base.metadata.tables.keys())
        expected_tables = {"users", "documents", "document_pages", "chunks", "queries", "document_access"}
        assert expected_tables.issubset(table_names)

    def test_document_foreign_keys(self):
        """Test Document has proper foreign keys."""
        fks = {fk.target_fullname for fk in Document.__table__.foreign_keys}
        assert "users.id" in fks

    def test_chunk_foreign_keys(self):
        """Test Chunk has proper foreign keys."""
        fks = {fk.target_fullname for fk in Chunk.__table__.foreign_keys}
        assert "documents.id" in fks
        assert "document_pages.id" in fks
