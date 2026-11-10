"""SQLAlchemy 2.0 ORM models for the Enterprise GenAI Data Intelligence Platform.

Tables
------
* **users** — platform users with role-based access
* **documents** — uploaded documents and their processing status
* **document_pages** — per-page extraction results
* **chunks** — text chunks with vector embeddings for RAG
* **queries** — user queries and generated answers with audit metadata
* **document_access** — per-document permission grants
"""

import enum
import uuid
from datetime import datetime

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):  # type: ignore[no-redef]
        """Fallback Vector type for environments without pgvector installed."""

        def __init__(self, dim: int):
            self.dim = dim

        def get_col_spec(self, **kw):
            return f"vector({self.dim})"
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Enums ────────────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    """Allowed user roles."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class DocumentStatus(str, enum.Enum):
    """Document processing lifecycle states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AccessPermission(str, enum.Enum):
    """Document-level permission types."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


# ── Declarative Base ────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


# ── Models ──────────────────────────────────────────────────────────────────


class User(Base):
    """Platform user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="uploader",
        lazy="selectin",
    )
    queries: Mapped[list["Query"]] = relationship(
        "Query",
        back_populates="user",
        lazy="selectin",
    )
    document_accesses: Mapped[list["DocumentAccess"]] = relationship(
        "DocumentAccess",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"


class Document(Base):
    """An uploaded document tracked through the processing pipeline."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", native_enum=False),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
    )
    extraction_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    uploader: Mapped["User"] = relationship("User", back_populates="documents")
    pages: Mapped[list["DocumentPage"]] = relationship(
        "DocumentPage",
        back_populates="document",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    accesses: Mapped[list["DocumentAccess"]] = relationship(
        "DocumentAccess",
        back_populates="document",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Document id={self.id} filename={self.filename!r}>"


class DocumentPage(Base):
    """Extracted content for a single page of a document."""

    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tables_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="pages")
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="page",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentPage id={self.id} doc={self.document_id} page={self.page_number}>"


class Chunk(Base):
    """A text chunk with its vector embedding, ready for RAG retrieval."""

    __tablename__ = "chunks"
    __table_args__ = (
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_chunks_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_pages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_clean: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(768), nullable=True)
    search_vector = mapped_column(TSVECTOR, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata_",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    page: Mapped["DocumentPage | None"] = relationship(
        "DocumentPage",
        back_populates="chunks",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Chunk id={self.id} doc={self.document_id} idx={self.chunk_index}>"


class Query(Base):
    """A user's RAG query and the generated answer with audit metadata."""

    __tablename__ = "queries"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    retrieval_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="queries")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Query id={self.id} user={self.user_id}>"


class DocumentAccess(Base):
    """Per-document permission grant linking a user to a document."""

    __tablename__ = "document_access"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission: Mapped[AccessPermission] = mapped_column(
        Enum(AccessPermission, name="access_permission", native_enum=False),
        nullable=False,
        default=AccessPermission.READ,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="accesses")
    user: Mapped["User"] = relationship("User", back_populates="document_accesses")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<DocumentAccess id={self.id} doc={self.document_id} "
            f"user={self.user_id} perm={self.permission}>"
        )
