"""Repository helpers for common CRUD and pagination operations."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from enterprise_ai.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository for SQLAlchemy ORM models.

    Repository classes own database access and query composition; services keep
    business rules. Transactions remain explicit so callers may decide when to
    commit or rollback a unit of work.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **data: Any) -> ModelType:
        """Create a new model record and return the flushed instance."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, record_id: uuid.UUID) -> ModelType | None:
        """Return a single model record by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: ColumnElement[Any] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """Return a list of rows, optionally filtered and ordered."""
        statement = select(self.model)
        if filters:
            for field_name, value in filters.items():
                if value is None:
                    continue
                statement = statement.where(getattr(self.model, field_name) == value)
        if order_by is not None:
            statement = statement.order_by(order_by)
        statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        max_page_size: int = 100,
        order_by: ColumnElement[Any] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelType], int, int]:
        """Return rows for a page and the total number of matching results."""
        safe_page = max(page, 1)
        safe_page_size = min(max(page_size, 1), max_page_size)
        total_query = select(func.count()).select_from(self.model)
        if filters:
            for field_name, value in filters.items():
                if value is None:
                    continue
                total_query = total_query.where(getattr(self.model, field_name) == value)
        total_result = await self.session.execute(total_query)
        total = total_result.scalar_one() or 0

        statement = select(self.model)
        if filters:
            for field_name, value in filters.items():
                if value is None:
                    continue
                statement = statement.where(getattr(self.model, field_name) == value)
        if order_by is not None:
            statement = statement.order_by(order_by)
        statement = statement.offset((safe_page - 1) * safe_page_size).limit(safe_page_size)
        result = await self.session.execute(statement)
        rows = list(result.scalars().all())
        return rows, total, safe_page_size

    async def update(self, record_id: uuid.UUID, **data: Any) -> ModelType | None:
        """Update a model instance with the supplied field values."""
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None
        for field_name, value in data.items():
            setattr(instance, field_name, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, record_id: uuid.UUID) -> bool:
        """Delete a single row by primary key and return whether it existed."""
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def count(self, *, filters: dict[str, Any] | None = None) -> int:
        """Count rows that match optional filters."""
        statement = select(func.count()).select_from(self.model)
        if filters:
            for field_name, value in filters.items():
                if value is None:
                    continue
                statement = statement.where(getattr(self.model, field_name) == value)
        result = await self.session.execute(statement)
        return int(result.scalar_one() or 0)
