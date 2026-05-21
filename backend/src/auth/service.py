"""Authentication business logic service."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import LoginRequest, RegisterRequest, UserAuthInfo
from src.auth.password import password_service
from src.database.table import User


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize auth service.

        Args:
            session: Async database session.
        """
        self.session = session

    async def register_user(self, request: RegisterRequest) -> User:
        """Register a new user.

        Args:
            request: User registration request data.

        Returns:
            Created User model.

        Raises:
            ValueError: If user already exists.
        """
        request.validate()

        # Check if user already exists
        existing_user = await self.session.execute(
            select(User).where(
                (User.email == request.email) | (User.name == request.name)
            )
        )
        if existing_user.scalar_one_or_none():
            raise ValueError('User with this email or name already exists')

        # Hash password and create user
        password_hash = password_service.hash_password(request.password)
        user = User(
            name=request.name,
            email=request.email,
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def authenticate_user(self, request: LoginRequest) -> User:
        """Authenticate user by email and password.

        Args:
            request: User login request data.

        Returns:
            Authenticated User model.

        Raises:
            ValueError: If credentials are invalid.
        """
        # Find user by email
        user = await self.session.execute(
            select(User).where(User.email == request.email)
        )
        user = user.scalar_one_or_none()

        if not user:
            raise ValueError('Invalid email or password')

        # Verify password
        if not password_service.verify_password(
            request.password, user.password_hash
        ):
            raise ValueError('Invalid email or password')

        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID to retrieve.

        Returns:
            User model or None if not found.
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def validate_token_expiry(exp: int) -> bool:
        """Validate if token expiration time is in the future.

        Args:
            exp: Unix timestamp of token expiration.

        Returns:
            True if token is still valid, False if expired.
        """
        return datetime.fromtimestamp(
            exp, tz=timezone.utc
        ) > datetime.now(tz=timezone.utc)

    @staticmethod
    def calculate_token_expiry(
        expiration_minutes: int,
    ) -> datetime:
        """Calculate token expiration datetime.

        Args:
            expiration_minutes: Number of minutes until expiration.

        Returns:
            Datetime when token will expire.
        """
        return datetime.now(tz=timezone.utc) + timedelta(
            minutes=expiration_minutes
        )
