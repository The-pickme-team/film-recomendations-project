from litestar.app import Litestar
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Server
from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from sqlalchemy.ext.asyncio import create_async_engine

from core.settings import config
from router.search import recommend_films, search_films_handler

app = Litestar(
    route_handlers=[
        search_films_handler,
        recommend_films,
    ],
    openapi_config=OpenAPIConfig(
        title=config.app.openapi.title,
        version=config.app.openapi.version,
        description=config.app.openapi.description,
        servers=[Server(url="/api")],
    ),
    cors_config=CORSConfig(
        allow_origins=config.app.cors.allowed_origins,
        allow_methods=config.app.cors.allowed_methods,
        allow_headers=config.app.cors.allowed_headers,
    ),
    compression_config=CompressionConfig(backend="brotli", brotli_gzip_fallback=True),
    plugins=[
        SQLAlchemyPlugin(
            SQLAlchemyAsyncConfig(
                engine_instance=create_async_engine(
                    config.database.url.composite(),
                    echo=True,
                    # === Connection pool ===
                    pool_size=config.database.pool_size,
                    max_overflow=config.database.max_overflow,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True,
                    pool_use_lifo=True,
                    # === Transaction isolation ===
                    isolation_level="READ COMMITTED",
                    # === Insert optimization ===
                    insertmanyvalues_page_size=1000,
                    use_insertmanyvalues=True,
                    # === Query cache ===
                    query_cache_size=1200,
                    # === Other ===
                    connect_args={},
                ),
                session_config=AsyncSessionConfig(
                    autoflush=False,
                    expire_on_commit=False,
                ),
            )
        )
    ],
)
