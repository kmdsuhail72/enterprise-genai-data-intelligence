"""Document ingestion service coordinating validation, storage, and persistence."""

import uuid
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentValidationError
from app.core.logging import get_logger
from app.db.models import Document, DocumentStatus
from app.db.repositories.documents import DocumentRepository
from app.ingestion.file_validator import FileValidator, FileValidationResult
from app.ingestion.storage import StorageBackend, get_storage_backend

logger = get_logger(__name__)


class IngestionService:
    """Enterprise document ingestion service."""

    def __init__(
        self,
        validator: FileValidator | None = None,
        storage: StorageBackend | None = None,
    ):
        self.validator = validator or FileValidator()
        self.storage = storage or get_storage_backend()

    async def ingest_document(
        self,
        session: AsyncSession,
        file_obj: BinaryIO,
        filename: str,
        uploaded_by: uuid.UUID,
    ) -> Document:
        """Validate, store, and create database record for an uploaded document."""
        # 1. Validate file
        validation_result: FileValidationResult = self.validator.validate(file_obj, filename)

        document_id = uuid.uuid4()

        # 2. Persist to storage backend
        storage_path = await self.storage.save(file_obj, filename, document_id)

        # 3. Create document record in database
        repo = DocumentRepository(session)
        doc = await repo.create(
            id=document_id,
            uploaded_by=uploaded_by,
            filename=filename,
            content_type=validation_result.mime_type,
            file_size_bytes=validation_result.file_size_bytes,
            storage_path=storage_path,
            status=DocumentStatus.PENDING,
            extraction_metadata={
                "extension": validation_result.extension,
                "mime_type": validation_result.mime_type,
            },
        )

        logger.info(
            "document_ingested",
            document_id=str(doc.id),
            filename=doc.filename,
            storage_path=storage_path,
        )
        return doc

