from datetime import datetime
from uuid import UUID

import msgspec
from litestar import get, post
from litestar.exceptions import HTTPException
from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.teble import Film, Vector


class FilmResponse(msgspec.Struct):  # noqa: D101
    id: UUID
    name: str
    description: str
    year_of_release: datetime
    genres: list[str]


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
    )


class RecommendRequest(msgspec.Struct):
    film_ids: list[UUID]
    limit_m: int = 10


class RecommendResponse(msgspec.Struct):
    id: UUID
    name: str
    final_score: float


@post('/films/recommend')
async def recommend_films(
    data: RecommendRequest, session: AsyncSession
) -> list[RecommendResponse]:
    n_ids = data.film_ids
    m_limit = data.limit_m

    # 1. Распаковываем жанры исходных N фильмов
    unnested_genres = (
        select(func.unnest(Film.genres).label('genre'))
        .where(Film.id.in_(n_ids))
        .cte('unnested_genres')
    )

    # 2. Считаем количество повторений каждого жанра
    genre_counts = (
        select(unnested_genres.c.genre, func.count().label('cnt'))
        .group_by(unnested_genres.c.genre)
        .cte('genre_counts')
    )

    # 3. Находим максимальное количество повторений (самый популярный жанр)
    max_count_sq = select(func.max(genre_counts.c.cnt)).scalar_subquery()

    # 4. Считаем нормализованный вес и сразу фильтруем те, где вес > 0.5
    # Формула: (количество / максимальное количество)
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

    # 5. Собираем отфильтрованные жанры в массив для эффективного поиска по GIN-индексу
    valid_genres_sq = select(
        func.array_agg(genre_weights.c.genre)
    ).scalar_subquery()

    # 6. Считаем средний вектор для исходных N фильмов
    avg_vector_sq = (
        select(func.avg(Vector.vector))
        .where(Vector.file_id.in_(n_ids))
        .scalar_subquery()
    )

    # 7. Подзапрос для подсчета суммы весов жанров конкретного фильма (для финальной формулы)
    # Используем column_valued для коррелированного подзапроса в SQLAlchemy 2.0
    genre_col = func.unnest(Film.genres).column_valued('genre')
    sum_weights_sq = (
        select(func.coalesce(func.sum(genre_weights.c.weight), 0.0))
        .select_from(genre_col)
        .join(genre_weights, genre_weights.c.genre == genre_col)
        .correlate(Film)
        .scalar_subquery()
    )

    # 8. Формируем финальную формулу
    # В pgvector оператор <=> возвращает косинусное расстояние.
    # Косинусное сходство вычисляется как (1 - расстояние).
    cosine_similarity = 1 - Vector.vector.op('<=>')(avg_vector_sq)
    genres_count = func.array_length(Film.genres, 1)

    final_score = sum_weights_sq + (cosine_similarity * genres_count)

    # 9. Главный запрос
    stmt = (
        select(Film.id, Film.name, final_score.label('score'))
        .join(Vector, Vector.file_id == Film.id)
        .where(
            # Ищем фильмы, имеющие хотя бы один жанр с весом > 0.5.
            # Метод overlap транслируется в оператор &&, который использует ваш GIN индекс
            Film.genres.overlap(valid_genres_sq),
            # Исключаем из выдачи фильмы, которые мы передали как исходные
            Film.id.not_in(n_ids),
        )
        .order_by(final_score.desc())
        .limit(m_limit)
    )

    # Выполняем запрос
    result = await session.execute(stmt)

    # Собираем ответ с помощью msgspec
    return [
        RecommendResponse(id=row.id, name=row.name, final_score=row.score)
        for row in result.all()
    ]
