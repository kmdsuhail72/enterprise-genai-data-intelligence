"""Repository logic for chat conversations and message history."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.database.base import Conversation, Message, MessageRole
from enterprise_ai.database.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """CRUD for conversation threads and their message history."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Conversation, session)

    async def create_conversation(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        title: str | None = None,
    ) -> Conversation:
        """Create a new conversation for a user and tenant."""
        return await self.create(user_id=user_id, tenant_id=tenant_id, title=title)

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Conversation]:
        """Return conversations belonging to a user."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_messages(
        self,
        *,
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Message]:
        """Return messages for a conversation in chronological order."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        *,
        conversation_id: uuid.UUID,
        role: str | MessageRole,
        content: str,
        citations: dict[str, object] | None = None,
        token_usage: dict[str, object] | None = None,
    ) -> Message:
        """Append a message to a conversation."""
        role_value = role if isinstance(role, MessageRole) else MessageRole(role)
        message = Message(
            conversation_id=conversation_id,
            role=role_value,
            content=content,
            citations=citations,
            token_usage=token_usage,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        *,
        title: str,
    ) -> Conversation | None:
        """Update a conversation title."""
        return await self.update(conversation_id, title=title)
