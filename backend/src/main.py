"""Main application entry point with JWT authentication setup."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar
from litestar.di import Provide

from src.api.router.auth import login, register
from src.api.router.search import (
    add_user_films,
    recommend_films,
    recommend_for_me,
    search_film,
)
from src.auth.token import token_service
from src.core.config import config
from src.database.session import Session


@asynccontextmanager
async def connection(app: Litestar) -> AsyncGenerator[None]:
    """Database connection lifespan manager."""
    Session.setap(
        config.api.database.url.encoded_string(),
        echo=config.api.dev,
    )
    yield
    await Session.dispose()
    print('Disconnecting from database...')


async def provide_session() -> AsyncGenerator:
    """Provide database session to route handlers."""
    async for session in Session.session():
        yield session


app = Litestar(
    route_handlers=[
        # Auth routes (public)
        register,
        login,
        # Search routes (require authentication)
        search_film,
        recommend_films,
        add_user_films,
        recommend_for_me,
    ],
    lifespan=[connection],
    dependencies={
        'session': Provide(provide_session),
    },
    middleware=[token_service.get_middleware()],
)
