from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar
from litestar.di import Provide

from src.api.router.search import recommend_films, search_film
from src.core.config import config
from src.database.session import Session


@asynccontextmanager
async def connection(app: Litestar) -> AsyncGenerator[None]:
    """Simulate a connection to a resource."""
    Session.setap(config.api.database.url.encoded_string(), echo=config.api.dev)
    yield
    await Session.dispose()
    print('Disconnecting from resource...')


app = Litestar(
    route_handlers=[search_film, recommend_films],
    lifespan=[connection],
    dependencies={
        'session': Provide(Session.session),
    },
)
