"""Document processing status lifecycle manager."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.base import Document, DocumentStatus
from enterprise_ai.database.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)


class StatusManager:
    """Manages document state transitions during ingestion and ETL pipelines."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DocumentRepository(session)

    async def set_processing(self, document_id: uuid.UUID) -> Document | None:
        """Mark document as processing."""
        logger.info("document_status_processing", document_id=str(document_id))
        return await self.repo.update_status(document_id, DocumentStatus.PROCESSING)

    async def set_completed(
        self,
        document_id: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> Document | None:
        """Mark document as successfully completed."""
        logger.info("document_status_completed", document_id=str(document_id))
        return await self.repo.update_status(document_id, DocumentStatus.COMPLETED, metadata)

    async def set_failed(
        self,
        document_id: uuid.UUID,
        error_message: str,
    ) -> Document | None:
        """Mark document as failed with diagnostic metadata."""
        logger.error("document_status_failed", document_id=str(document_id), error=error_message)
        return await self.repo.update_status(
            document_id,
            DocumentStatus.FAILED,
            {"error": error_message},
        )

