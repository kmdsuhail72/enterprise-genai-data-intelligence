"""User service coordinating authentication, registration, and role assignment."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.core.exceptions import DuplicateRecordError, InvalidCredentialsError
from enterprise_ai.core.logging import get_logger
from enterprise_ai.core.security import create_access_token, get_password_hash, verify_password
from enterprise_ai.database.base import User, UserRole
from enterprise_ai.database.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:
    """Coordinates user management and authentication."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        """Register a new user account."""
        if await self.user_repo.email_exists(email):
            raise DuplicateRecordError(f"User with email '{email}' already exists.")

        user = await self.user_repo.create(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        logger.info("user_registered", user_id=str(user.id), email=email, role=role.value)
        return user

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user and return JWT access token."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")

        token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }

