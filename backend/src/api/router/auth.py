"""Authentication API routes following SOLID principles."""

from litestar import post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.auth.service import AuthService
from src.auth.token import token_service


@post('/auth/register', status_code=HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession,
) -> TokenResponse:
    """Register a new user and return JWT token.

    Args:
        data: User registration request data.
        session: Database session.

    Returns:
        Token response with access token.

    Raises:
        ValueError: If registration data is invalid or user exists.
    """
    auth_service = AuthService(session)

    try:
        # Register user (AuthService handles user creation + password hashing)
        user = await auth_service.register_user(data)
        await session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail='User with this email or name already exists',
        ) from exc

    # TokenService handles token creation (DRY principle)
    return token_service.create_access_token(
        user_id=user.id,
        email=user.email,
    )


@post('/auth/login')
async def login(
    data: LoginRequest,
    session: AsyncSession,
) -> LoginResponse:
    """Authenticate user and return JWT token with user data.

    Args:
        data: User login request data.
        session: Database session.

    Returns:
        Login response with user data and token.

    Raises:
        ValueError: If credentials are invalid.
    """
    auth_service = AuthService(session)

    try:
        # Authenticate user (validates email and password)
        user = await auth_service.authenticate_user(data)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    # TokenService handles token creation (DRY principle)
    access_token = token_service.create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return LoginResponse(
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
        ),
        token=access_token,
    )
