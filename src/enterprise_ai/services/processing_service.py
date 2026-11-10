"""Background document processing orchestration service coordinating extraction and database storage."""

import io
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.exceptions import DocumentNotFoundError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.database.base import DocumentPage, DocumentStatus
from enterprise_ai.database.repositories.document_repository import DocumentRepository
from enterprise_ai.extraction.router import ExtractionRouter, get_extraction_router
from enterprise_ai.extraction.schemas import ExtractedDocument
from enterprise_ai.ingestion.local_storage import LocalStorage
from enterprise_ai.ingestion.s3_storage import S3Storage
from enterprise_ai.ingestion.status_manager import StatusManager
from enterprise_ai.ingestion.storage_interface import StorageInterface

logger = get_logger(__name__)


class ProcessingService:
    """Coordinates asynchronous document parsing, extraction, and database persistence."""

    def __init__(
        self,
        session: AsyncSession,
        router: ExtractionRouter | None = None,
        storage: StorageInterface | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.status_manager = StatusManager(session)
        self.router = router or get_extraction_router()
        self.storage = storage or LocalStorage()

    async def process_document(
        self,
        document_id: uuid.UUID,
        options: dict | None = None,
    ) -> ExtractedDocument:
        """Execute end-to-end extraction pipeline for a stored document."""
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {document_id} was not found.")

        # Transition status to PROCESSING
        await self.status_manager.set_processing(document_id)

        try:
            # 1. Read file from storage
            file_bytes = await self.storage.read(doc.storage_path)
            file_obj = io.BytesIO(file_bytes)

            # 2. Extract structured content
            extracted_doc: ExtractedDocument = await self.router.extract(
                file_obj=file_obj,
                filename=doc.filename,
                options=options,
            )
            extracted_doc.document_id = document_id

            # 3. Persist ExtractedPages to database
            for page in extracted_doc.pages:
                tables_data = [
                    {
                        "table_index": t.table_index,
                        "headers": t.headers,
                        "rows": t.rows,
                        "title": t.title,
                        "sheet_name": t.sheet_name,
                    }
                    for t in page.tables
                ]

                db_page = DocumentPage(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    page_number=page.page_number,
                    raw_text=page.raw_text,
                    cleaned_text=page.cleaned_text,
                    extraction_method=page.extraction_method,
                    tables_json={"tables": tables_data} if tables_data else None,
                )
                self.session.add(db_page)

            # 4. Update document metadata and mark COMPLETED
            metadata = {
                "total_pages": extracted_doc.total_pages,
                "file_type": extracted_doc.file_type,
                "table_count": sum(len(p.tables) for p in extracted_doc.pages),
                "total_words": sum(p.word_count for p in extracted_doc.pages),
                "total_chars": sum(p.char_count for p in extracted_doc.pages),
                **(doc.extraction_metadata or {}),
                **extracted_doc.metadata,
            }

            await self.status_manager.set_completed(document_id, metadata)
            await self.session.commit()

            logger.info(
                "document_processing_succeeded",
                document_id=str(document_id),
                total_pages=extracted_doc.total_pages,
                table_count=metadata["table_count"],
            )
            return extracted_doc

        except Exception as exc:
            logger.error(
                "document_processing_failed",
                document_id=str(document_id),
                error=str(exc),
            )
            await self.status_manager.set_failed(document_id, str(exc))
            await self.session.commit()
            raise
