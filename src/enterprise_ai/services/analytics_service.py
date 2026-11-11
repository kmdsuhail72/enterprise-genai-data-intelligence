"""Analytics service coordinating deterministic numerical computations and summaries."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.repositories.chunk_repository import ChunkRepository
from enterprise_ai.database.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class AnalyticsService:
    """Coordinates business intelligence queries, financial calculations, and reports."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)

    async def get_system_summary(self) -> dict[str, Any]:
        """Aggregate high-level system usage metrics."""
        total_documents = await self.doc_repo.count()
        total_chunks = await self.chunk_repo.count()
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "system_status": "operational",
        }

