from datetime import datetime
from uuid import UUID
from typing import Optional

import msgspec
from litestar import get, post
from litestar.connection import ASGIConnection
from litestar.datastructures import UploadFile
from litestar.exceptions import HTTPException
from litestar.response import Response
from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.teble import Film, User, Vector


class FilmResponse(msgspec.Struct):  # noqa: D101
    id: UUID
    name: str
    description: str
    year_of_release: datetime
    genres: list[str]
    # image binary is returned via dedicated endpoints
    image: Optional[str]


class RecommendRequest(msgspec.Struct):
    film_ids: list[UUID]
    limit_m: int = 10


class RecommendResponse(msgspec.Struct):
    id: UUID
    name: str
    final_score: float


class AddUserFilmsRequest(msgspec.Struct):
    film_ids: list[UUID]


class AddUserFilmsResponse(msgspec.Struct):
    added: int
    total: int


@get('/films/<name:str>')
async def search_film(name: str, session: AsyncSession) -> FilmResponse:
    """Search for films by name."""
    if (
        result := await session.scalar(
            select(Film).where(Film.name.ilike(f'%{name}%'))
        )
    ) is None:
        raise HTTPException(status_code=404, detail='Film not found')

    return FilmResponse(
        id=result.id,
        name=result.name,
        description=result.description,
        year_of_release=result.year_of_release,
        genres=result.genres,
        image=None,
    )


@post('/films/<film_id:uuid>/image')
async def upload_film_image(
    film_id: UUID, file: UploadFile, session: AsyncSession
):
    """Upload binary image for a film and store it in DB."""
    film = await session.scalar(select(Film).where(Film.id == film_id))
    if film is None:
        raise HTTPException(status_code=404, detail='Film not found')

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail='Empty file')

    film.image_data = data
    await session.commit()

    return {'uploaded': True}


@get('/films/<film_id:uuid>/image')
async def download_film_image(film_id: UUID, session: AsyncSession) -> Response:
    """Return stored image binary as a downloadable file."""
    film = await session.scalar(select(Film).where(Film.id == film_id))
    if film is None:
        raise HTTPException(status_code=404, detail='Film not found')
    if not film.image_data:
        raise HTTPException(status_code=404, detail='Image not found')

    headers = {'Content-Disposition': f'attachment; filename="{film.name}.bin"'}
    return Response(content=film.image_data, media_type='application/octet-stream', headers=headers)


def _build_recommendation_statement(
    film_ids: list[UUID],
    limit_m: int,
):
    """Build the shared recommendation query for a seed film set."""
    unnested_genres = (
        select(func.unnest(Film.genres).label('genre'))
        .where(Film.id.in_(film_ids))
        .cte('unnested_genres')
    )

    genre_counts = (
        select(unnested_genres.c.genre, func.count().label('cnt'))
        .group_by(unnested_genres.c.genre)
        .cte('genre_counts')
    )

    max_count_sq = select(func.max(genre_counts.c.cnt)).scalar_subquery()

    genre_weights = (
        select(
            genre_counts.c.genre,
            (cast(genre_counts.c.cnt, Float) / cast(max_count_sq, Float)).label(
                'weight'
            ),
        )
        .where(
            (cast(genre_counts.c.cnt, Float) / cast(max_count_sq, Float)) > 0.5
        )
        .cte('genre_weights')
    )

    valid_genres_sq = select(func.array_agg(genre_weights.c.genre)).scalar_subquery()

    avg_vector_sq = (
        select(func.avg(Vector.vector))
        .where(Vector.file_id.in_(film_ids))
        .scalar_subquery()
    )

    genre_col = func.unnest(Film.genres).column_valued('genre')
    sum_weights_sq = (
        select(func.coalesce(func.sum(genre_weights.c.weight), 0.0))
        .select_from(genre_col)
        .join(genre_weights, genre_weights.c.genre == genre_col)
        .correlate(Film)
        .scalar_subquery()
    )

    cosine_similarity = 1 - Vector.vector.op('<=>')(avg_vector_sq)
    genres_count = func.array_length(Film.genres, 1)
    final_score = sum_weights_sq + (cosine_similarity * genres_count)

    return (
        select(Film.id, Film.name, final_score.label('score'))
        .join(Vector, Vector.file_id == Film.id)
        .where(
            Film.genres.overlap(valid_genres_sq),
            Film.id.not_in(film_ids),
        )
        .order_by(final_score.desc())
        .limit(limit_m)
    )


@post('/films/recommend')
async def recommend_films(
    data: RecommendRequest, session: AsyncSession
) -> list[RecommendResponse]:
    result = await session.execute(
        _build_recommendation_statement(data.film_ids, data.limit_m)
    )

    return [
        RecommendResponse(id=row.id, name=row.name, final_score=row.score)
        for row in result.all()
    ]


@post('/users/me/films')
async def add_user_films(
    data: AddUserFilmsRequest,
    session: AsyncSession,
    connection: ASGIConnection,
) -> AddUserFilmsResponse:
    """Add films to the authenticated user's list."""
    if not data.film_ids:
        raise HTTPException(status_code=400, detail='film_ids cannot be empty')

    user_id = UUID(str(connection.user.user_id))
    user = await session.scalar(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.films))
    )
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    requested_ids = list(dict.fromkeys(data.film_ids))
    films_result = await session.scalars(
        select(Film).where(Film.id.in_(requested_ids))
    )
    films_list = list(films_result.all())
    if len(films_list) != len(requested_ids):
        raise HTTPException(status_code=404, detail='One or more films not found')

    existing_ids = {film.id for film in user.films}
    new_films = [film for film in films_list if film.id not in existing_ids]

    if new_films:
        user.films.extend(new_films)
        await session.commit()

    return AddUserFilmsResponse(added=len(new_films), total=len(user.films))


@get('/users/me/recommend')
async def recommend_for_me(
    session: AsyncSession,
    connection: ASGIConnection,
    limit_m: int = 10,
) -> list[RecommendResponse]:
    """Recommend films from the authenticated user's saved films."""
    user_id = UUID(str(connection.user.user_id))
    user = await session.scalar(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.films))
    )
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    film_ids = [film.id for film in user.films]
    if not film_ids:
        raise HTTPException(
            status_code=400,
            detail='Add films to your profile before requesting recommendations',
        )

    result = await session.execute(
        _build_recommendation_statement(film_ids, limit_m)
    )

    return [
        RecommendResponse(id=row.id, name=row.name, final_score=row.score)
        for row in result.all()
    ]
