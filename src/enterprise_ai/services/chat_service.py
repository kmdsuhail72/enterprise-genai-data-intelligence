"""Chat service coordinating RAG queries, evidence retrieval, and conversation audit records."""

import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.base import Query
from enterprise_ai.database.repositories.chunk_repository import ChunkRepository

logger = get_logger(__name__)


class ChatService:
    """Coordinates RAG queries, context retrieval, and model answers."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunk_repo = ChunkRepository(session)

    async def execute_query(
        self,
        question: str,
        user_id: uuid.UUID,
        document_ids: list[uuid.UUID] | None = None,
    ) -> dict[str, Any]:
        """Execute RAG query pipeline and record query audit trail."""
        start_time = time.perf_counter()

        # Hybrid/Vector retrieval stub for service orchestration
        # (Concrete RAG pipeline connects here in subsequent phase)
        retrieved_chunks = await self.chunk_repo.full_text_search(
            query=question,
            top_k=5,
            document_ids=document_ids,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        query_record = Query(
            id=uuid.uuid4(),
            user_id=user_id,
            question=question,
            answer="Answer generation pipeline initialized.",
            citations={"sources": [c["chunk_id"] for c in retrieved_chunks]},
            retrieval_metadata={"num_retrieved": len(retrieved_chunks)},
            latency_ms=latency_ms,
        )
        self.session.add(query_record)
        await self.session.flush()

        return {
            "query_id": str(query_record.id),
            "question": question,
            "answer": query_record.answer,
            "citations": query_record.citations,
            "latency_ms": latency_ms,
        }

