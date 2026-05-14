"""Authentication data models and request/response schemas."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from msgspec import Struct


@dataclass
class UserAuthInfo:
    """User authentication information from JWT token."""

    user_id: UUID
    email: str


class TokenResponse(Struct):
    """Response model for token authentication."""

    access_token: str
    expires_in: int  # seconds
    token_type: str = 'bearer'


class UserResponse(Struct):
    """Response model for user data."""

    id: UUID
    name: str
    email: str
    created_at: datetime


class RegisterRequest(Struct):
    """Request model for user registration."""

    name: str
    email: str
    password: str

    def validate(self) -> None:
        """Validate registration request.

        Raises:
            ValueError: If validation fails.
        """
        if not self.name or len(self.name) < 2:
            raise ValueError('Name must be at least 2 characters long')
        if not self.email or '@' not in self.email:
            raise ValueError('Invalid email address')
        if not self.password or len(self.password) < 8:
            raise ValueError('Password must be at least 8 characters long')


class LoginRequest(Struct):
    """Request model for user login."""

    email: str
    password: str


class LoginResponse(Struct):
    """Response model for login endpoint."""

    user: UserResponse
    token: TokenResponse
