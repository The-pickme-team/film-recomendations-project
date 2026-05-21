from pgvector.asyncpg import register_vector
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)


class Session:
    """Async database session manager."""

    __active = False

    @classmethod
    def setup(cls, url: str, *, echo: bool = False):
        """Configure the async database engine and session factory."""
        cls.__engine = create_async_engine(
            url,
            echo=echo,
            future=True,
            # === Connection pool ===
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            pool_use_lifo=True,
            # === Transaction isolation ===
            isolation_level='READ COMMITTED',
            # === Insert optimization ===
            insertmanyvalues_page_size=1000,
            use_insertmanyvalues=True,
            # === Query cache ===
            query_cache_size=1200,
            # === Other ===
            connect_args={},
        )

        @event.listens_for(cls.__engine.sync_engine, 'connect')
        def connect(dbapi_connection, connection_record):
            dbapi_connection.run_async(register_vector)

        cls.__session_factory = async_sessionmaker(
            bind=cls.__engine, autoflush=False, expire_on_commit=False
        )
        cls.__active = True

    @classmethod
    async def dispose(cls):
        """Dispose of the async database engine and cleanup resources."""
        if not cls.__active:
            raise RuntimeError('Session is not active. Call setup() first.')

        await cls.__engine.dispose()

    @classmethod
    async def session(cls):
        """Create and return a new async session instance."""
        if not cls.__active:
            raise RuntimeError('Session is not active. Call setap() first.')

        session = cls.__session_factory()
        try:
            yield session
        except BaseException:
            await session.rollback()
            raise
        finally:
            await session.close()
