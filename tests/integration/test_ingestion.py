"""Integration test for document ingestion, storage, extraction, and database persistence."""

import io
import uuid
import pytest
from sqlalchemy import select

from enterprise_ai.database.base import Document, DocumentPage, DocumentStatus, User, UserRole
from enterprise_ai.database.connection import async_session_factory
from enterprise_ai.ingestion.ingestion_service import IngestionService
from enterprise_ai.services.processing_service import ProcessingService


@pytest.mark.asyncio
async def test_full_ingestion_and_processing_pipeline():
    """Test full document lifecycle: Ingest -> LocalStorage -> Extraction -> DB Pages."""
    session = await async_session_factory()
    try:
        # 1. Create a test user in DB for relational integrity
        test_user_id = uuid.uuid4()
        user = User(
            id=test_user_id,
            email=f"data.engineer_{test_user_id.hex[:8]}@enterprise.ai",
            hashed_password="bcrypt_hashed_password_sample",
            full_name="Integration Test User",
            role=UserRole.ANALYST,
            is_active=True,
        )
        session.add(user)
        await session.commit()

        # 2. Ingest CSV document
        csv_content = (
            "Metric,FY2022,FY2023,YoY_Growth\n"
            "Cloud Revenue,120.5,185.2,+53.7%\n"
            "Operating Margin,22.4%,28.1%,+5.7pts\n"
            "Headcount,1420,1850,+30.3%\n"
        ).encode("utf-8")

        ingestion_service = IngestionService()
        doc = await ingestion_service.ingest_document(
            session=session,
            file_obj=io.BytesIO(csv_content),
            filename="financial_kpis.csv",
            uploaded_by=test_user_id,
        )
        await session.commit()

        assert doc.id is not None
        assert doc.status == DocumentStatus.PENDING
        assert doc.filename == "financial_kpis.csv"
        assert doc.file_size_bytes == len(csv_content)

        # 3. Process the document
        processing_service = ProcessingService(session=session)
        extracted = await processing_service.process_document(doc.id)

        assert extracted.total_pages == 1
        assert len(extracted.pages) == 1
        assert len(extracted.pages[0].tables) == 1

        # 4. Verify database state
        refreshed_doc = await session.get(Document, doc.id)
        assert refreshed_doc.status == DocumentStatus.COMPLETED
        assert refreshed_doc.extraction_metadata["table_count"] == 1
        assert refreshed_doc.extraction_metadata["file_type"] == "csv"

        # Verify DocumentPage rows
        stmt = select(DocumentPage).where(DocumentPage.document_id == doc.id)
        result = await session.execute(stmt)
        pages = list(result.scalars().all())

        assert len(pages) == 1
        page = pages[0]
        assert page.page_number == 1
        assert page.extraction_method == "csv"
        assert "Cloud Revenue" in page.cleaned_text
        assert page.tables_json is not None
        assert "tables" in page.tables_json
        assert page.tables_json["tables"][0]["headers"] == ["Metric", "FY2022", "FY2023", "YoY_Growth"]

    finally:
        await session.close()
