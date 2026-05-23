from datetime import datetime
from typing import Any
from uuid import UUID

from litestar import get, post
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.table import Film, Vector


class FilmSearchResponse(BaseModel):
    id: UUID
    name: str
    description: str
    year_of_release: datetime
    image_path: str
    genres: list[str]


def _to_search_response(film: Film) -> FilmSearchResponse:
    return FilmSearchResponse(
        id=film.id,
        name=film.name,
        description=film.description,
        year_of_release=film.year_of_release,
        image_path=film.image_path,
        genres=film.genres,
    )


@get("/films/search")
async def search_films_handler(
    db_session: AsyncSession,
    film_name: str,
) -> list[FilmSearchResponse]:
    statement = (
        select(Film)
        .where(Film.name.ilike(f"%{film_name}%"))
        .order_by(Film.year_of_release.desc())
    )

    films = (await db_session.scalars(statement)).all()
    return [_to_search_response(film) for film in films]


@post("/films/recommend")
async def recommend_films(
    db_session: AsyncSession,
    film_ids: list[UUID],
    limit: int = 10,
) -> list[FilmSearchResponse]:
    film_ids = list(dict.fromkeys(film_ids))
    if not film_ids:
        return []

    avg_vector_subq = (
        select(func.avg(Vector.vector))
        .where(Vector.file_id.in_(film_ids))
        .scalar_subquery()
    )

    candidates_statement = (
        select(Film)
        .join(Vector, Vector.file_id == Film.id)
        .where(Film.id.notin_(film_ids))
        .order_by(Vector.vector.cosine_distance(avg_vector_subq))
        .limit(limit)
    )
    films = (await db_session.scalars(candidates_statement)).all()
    return [_to_search_response(film) for film in films]
