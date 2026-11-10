"""User-specific repository with domain queries."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.database.base import User, UserRole
from enterprise_ai.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Look up user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Return active users."""
        result = await self.session.execute(
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Return users by role."""
        result = await self.session.execute(
            select(User)
            .where(User.role == role)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def deactivate(self, user_id: uuid.UUID) -> User | None:
        """Deactivate a user account."""
        return await self.update(user_id, is_active=False)

    async def activate(self, user_id: uuid.UUID) -> User | None:
        """Activate a user account."""
        return await self.update(user_id, is_active=True)

    async def email_exists(self, email: str) -> bool:
        """Check if user email already exists."""
        user = await self.get_by_email(email)
        return user is not None
