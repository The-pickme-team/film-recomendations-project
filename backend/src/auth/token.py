"""Token management service with SOLID principles."""

from datetime import timedelta
from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth

from src.auth.models import TokenResponse, UserAuthInfo
from src.core.config import config


class TokenService:
    """Service for JWT token creation and validation.
    
    Implements Single Responsibility Principle - only manages tokens.
    Designed to be extended for refresh tokens, API keys, etc.
    """

    def __init__(self) -> None:
        """Initialize token service with JWT auth instance."""
        self._jwt_auth = self._create_jwt_auth()

    @staticmethod
    def _create_jwt_auth() -> JWTAuth[UserAuthInfo]:
        """Create and configure JWT authentication instance.
        
        Centralizes JWT configuration to avoid duplication.
        Can be overridden for testing or alternative implementations.
        
        Returns:
            Configured JWTAuth instance.
        """
        return JWTAuth[UserAuthInfo](
            token_secret=config.api.jwt.secret,
            algorithm=config.api.jwt.algorithm,
            retrieve_user_handler=_retrieve_user,
            default_token_expiration=timedelta(
                minutes=config.api.jwt.expiration_minutes,
            ),
            exclude=['/auth/register', '/auth/login', '/schema'],  # Public endpoints
        )

    def create_access_token(
        self,
        user_id: UUID,
        email: str,
    ) -> TokenResponse:
        """Create JWT access token for user.
        
        Encapsulates token creation logic following DRY principle.
        Can be extended to support refresh tokens, scopes, etc.
        
        Args:
            user_id: User ID to include in token.
            email: User email to include in token claims.
        
        Returns:
            TokenResponse with access token and expiration.
        """
        encoded_token = self._jwt_auth.create_token(
            identifier=str(user_id),
            token_extras={'email': email},
        )

        return TokenResponse(
            access_token=encoded_token,
            expires_in=config.api.jwt.expiration_minutes * 60,
        )

    def get_middleware(self):
        """Get JWT middleware for application.
        
        Returns:
            Configured JWT middleware instance.
        """
        return self._jwt_auth.middleware

    def get_exclude_patterns(self) -> list[str]:
        """Get URL patterns that should be excluded from JWT validation.
        
        Returns:
            List of URL patterns to exclude.
        """
        return ['/auth/register', '/auth/login', '/schema']


async def _retrieve_user(
    token: dict, _connection: ASGIConnection,
) -> UserAuthInfo:
    """Extract user info from JWT token payload.

    Args:
        token: Decoded JWT token payload.
        _connection: ASGI connection object.

    Returns:
        User authentication info.
    """
    return UserAuthInfo(
        user_id=token['sub'],
        email=token.get('email', ''),
    )


# Singleton instance for application use
token_service = TokenService()
