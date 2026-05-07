from datetime import datetime
from uuid import UUID, uuid7

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import ARRAY, ForeignKey, Index, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ID:
    """Base class for models with an ID primary key."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)


class Time:
    """Base class for models with created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class BaseTable(DeclarativeBase):
    """Base declarative class for ORM models."""

    metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s',
        }
    )


class Film(BaseTable, ID, Time):
    """ORM model for stored file metadata."""

    __tablename__ = 'films'

    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    year_of_release: Mapped[datetime] = mapped_column()

    genres: Mapped[list[str]] = mapped_column(ARRAY(String))
    vector: Mapped[Vector] = relationship()

    __table_args__ = (
        Index('ix_movie_genres_gin', 'genres', postgresql_using='gin'),
    )


class Vector(BaseTable, ID, Time):
    """ORM model for vector metadata."""

    __tablename__ = 'vectors'

    file_id: Mapped[UUID] = mapped_column(
        ForeignKey('films.id'), primary_key=True
    )
    vector: Mapped[list[float]] = mapped_column(HALFVEC(1024))
    model: Mapped[str] = mapped_column()

    __table_args__ = (
        Index(
            'idx_vectors_hnsw_cosine',
            'vector',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'vector': 'halfvec_cosine_ops'},
        ),
    )
