"""Pydantic schemas for authentication and user management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    full_name: str


class UserLoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str
    role: str


class UserResponse(BaseModel):
    """Schema for user representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

