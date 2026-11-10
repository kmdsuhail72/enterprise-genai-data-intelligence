"""Document-specific repository with domain queries."""

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.database.base import Document, DocumentStatus
from enterprise_ai.database.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Document, session)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """Return documents uploaded by a specific user."""
        result = await self.session.execute(
            select(Document)
            .where(Document.uploaded_by == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: DocumentStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """Return documents with a given processing status."""
        result = await self.session.execute(
            select(Document)
            .where(Document.status == status)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        extraction_metadata: dict[str, Any] | None = None,
    ) -> Document | None:
        """Transition document status and optional extraction metadata."""
        values: dict[str, Any] = {"status": status}
        if extraction_metadata is not None:
            values["extraction_metadata"] = extraction_metadata

        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(**values)
        )
        await self.session.flush()
        return await self.get_by_id(document_id)

    async def get_pending_documents(self, limit: int = 50) -> list[Document]:
        """Return documents pending processing."""
        return await self.get_by_status(DocumentStatus.PENDING, limit=limit)

    async def get_by_filename(self, filename: str) -> list[Document]:
        """Search documents by filename."""
        result = await self.session.execute(
            select(Document)
            .where(Document.filename == filename)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())
