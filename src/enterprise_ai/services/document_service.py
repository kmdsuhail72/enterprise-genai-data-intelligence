"""Document service coordinating ingestion, document queries, and deletion."""

import uuid
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.exceptions import DocumentNotFoundError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.base import Document
from enterprise_ai.database.repositories.chunk_repository import ChunkRepository
from enterprise_ai.database.repositories.document_repository import DocumentRepository
from enterprise_ai.ingestion.ingestion_service import IngestionService
from enterprise_ai.ingestion.local_storage import LocalStorage

logger = get_logger(__name__)


class DocumentService:
    """Coordinates document operations between API routes, ingestion, and repositories."""

    def __init__(
        self,
        session: AsyncSession,
        ingestion_service: IngestionService | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.ingestion_service = ingestion_service or IngestionService()

    async def upload_document(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: uuid.UUID,
    ) -> Document:
        """Upload and ingest a document."""
        return await self.ingestion_service.ingest_document(
            session=self.session,
            file_obj=file_obj,
            filename=filename,
            uploaded_by=user_id,
        )

    async def get_document(self, document_id: uuid.UUID) -> Document:
        """Fetch a document by ID or raise DocumentNotFoundError."""
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {document_id} was not found.")
        return doc

    async def list_documents(self, user_id: uuid.UUID | None = None, skip: int = 0, limit: int = 50) -> list[Document]:
        """List documents, optionally filtered by user."""
        if user_id:
            return await self.doc_repo.get_by_user(user_id, skip=skip, limit=limit)
        return await self.doc_repo.get_all(skip=skip, limit=limit)

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete document record, its chunks, and underlying storage file."""
        doc = await self.get_document(document_id)
        # Delete associated chunks
        await self.chunk_repo.delete_by_document_id(document_id)
        # Delete file from storage
        storage = LocalStorage()
        await storage.delete(doc.storage_path)
        # Delete record
        return await self.doc_repo.delete(document_id)

