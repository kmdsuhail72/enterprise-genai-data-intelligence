"""Document ingestion service coordinating validation, storage, and persistence."""

import uuid
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.base import Document, DocumentStatus
from enterprise_ai.database.repositories.document_repository import DocumentRepository
from enterprise_ai.ingestion.local_storage import LocalStorage
from enterprise_ai.ingestion.s3_storage import S3Storage
from enterprise_ai.ingestion.storage_interface import StorageInterface
from enterprise_ai.ingestion.upload_service import UploadService

logger = get_logger(__name__)


class IngestionService:
    """Enterprise document ingestion service."""

    def __init__(
        self,
        upload_service: UploadService | None = None,
    ):
        self.upload_service = upload_service or UploadService()

    async def ingest_document(
        self,
        session: AsyncSession,
        file_obj: BinaryIO,
        filename: str,
        uploaded_by: uuid.UUID,
    ) -> Document:
        """Validate, store, and create database record for an uploaded document."""
        document_id = uuid.uuid4()

        validation_result, storage_path, checksum = await self.upload_service.handle_upload(
            file_obj=file_obj,
            filename=filename,
            document_id=document_id,
        )

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
                "sha256": checksum,
            },
        )

        logger.info(
            "document_ingested",
            document_id=str(doc.id),
            filename=doc.filename,
            storage_path=storage_path,
            checksum=checksum,
        )
        return doc

