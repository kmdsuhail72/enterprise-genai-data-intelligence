"""Chunk-specific repository with vector and hybrid search support."""

import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.database.base import Chunk
from enterprise_ai.database.repositories.base import BaseRepository


class ChunkRepository(BaseRepository[Chunk]):
    """Repository for Chunk operations including vector search."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Chunk, session)

    async def get_by_document_id(
        self,
        document_id: uuid.UUID,
        skip: int = 0,
        limit: int = 500,
    ) -> list[Chunk]:
        """Return all chunks belonging to a document, ordered by index."""
        result = await self.session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_create(self, chunks: list[dict[str, Any]]) -> list[Chunk]:
        """Insert multiple chunks in a single flush."""
        instances: list[Chunk] = []
        for chunk_data in chunks:
            instance = Chunk(**chunk_data)
            self.session.add(instance)
            instances.append(instance)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        document_ids: list[uuid.UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform cosine-similarity vector search over chunk embeddings."""
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        filters = ""
        params: dict[str, Any] = {
            "embedding": embedding_str,
            "top_k": top_k,
        }

        if document_ids:
            placeholders = ", ".join(f":doc_id_{i}" for i in range(len(document_ids)))
            filters = f"AND c.document_id IN ({placeholders})"
            for i, doc_id in enumerate(document_ids):
                params[f"doc_id_{i}"] = str(doc_id)

        sql = text(f"""
            SELECT
                c.id,
                c.document_id,
                c.page_id,
                c.chunk_index,
                c.content,
                c.content_clean,
                c.metadata_,
                c.created_at,
                c.embedding <=> :embedding ::vector AS distance
            FROM chunks c
            WHERE c.embedding IS NOT NULL
            {filters}
            ORDER BY distance ASC
            LIMIT :top_k
        """)

        result = await self.session.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "page_id": row.page_id,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "content_clean": row.content_clean,
                "metadata_": row.metadata_,
                "created_at": row.created_at,
                "distance": row.distance,
            }
            for row in rows
        ]

    async def full_text_search(
        self,
        query: str,
        top_k: int = 10,
        document_ids: list[uuid.UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform PostgreSQL full-text search over the search_vector column."""
        filters = ""
        params: dict[str, Any] = {
            "query": query,
            "top_k": top_k,
        }

        if document_ids:
            placeholders = ", ".join(f":doc_id_{i}" for i in range(len(document_ids)))
            filters = f"AND c.document_id IN ({placeholders})"
            for i, doc_id in enumerate(document_ids):
                params[f"doc_id_{i}"] = str(doc_id)

        sql = text(f"""
            SELECT
                c.id,
                c.document_id,
                c.chunk_index,
                c.content,
                ts_rank(c.search_vector, plainto_tsquery('english', :query)) AS rank
            FROM chunks c
            WHERE c.search_vector @@ plainto_tsquery('english', :query)
            {filters}
            ORDER BY rank DESC
            LIMIT :top_k
        """)

        result = await self.session.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "rank": row.rank,
            }
            for row in rows
        ]

    async def delete_by_document_id(self, document_id: uuid.UUID) -> int:
        """Delete all chunks for a document."""
        from sqlalchemy import delete as sa_delete

        result = await self.session.execute(
            sa_delete(Chunk).where(Chunk.document_id == document_id)
        )
        rowcount = getattr(result, "rowcount", 0) or 0
        return int(rowcount)
