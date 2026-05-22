from collections import Counter
from datetime import datetime
from uuid import UUID

from litestar import get, post
from pydantic import BaseModel
from sqlalchemy import case, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.teble import Film, Vector

class FilmSearchResponse(BaseModel):
    id: UUID
    name: str
    description: str
    year_of_release: datetime
    image_path: str
    genres: list[str]


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
    return [
        FilmSearchResponse(
            id=film.id,
            name=film.name,
            description=film.description,
            year_of_release=film.year_of_release,
            image_path=film.image_path,
            genres=film.genres,
        )
        for film in films
    ]


async def _get_seed_genres_and_vector(film_ids: list[UUID], db_session: AsyncSession):
    # 1. Получаем векторы
    vector_result = await db_session.execute(
        select(Vector.vector).where(Vector.file_id.in_(film_ids))
    )
    # Оставляем только те, что не None
    vectors = [row[0] for row in vector_result.all() if row[0] is not None]

    if not vectors:
        print(f"DEBUG: Вектори не знайдені для ID: {film_ids}")
        return None, {}

    try:
        # Пытаемся вычислить среднее
        # Если здесь ошибка размерности, мы ее увидим в логах
        avg_vector = [sum(v[i] for v in vectors) / len(vectors) for i in range(len(vectors[0]))]
    except Exception as e:
        print(f"DEBUG: Помилка обчислення вектора: {e}")
        return None, {}

    # 2. Получаем жанры
    film_result = await db_session.execute(
        select(Film.genres).where(Film.id.in_(film_ids))
    )
    
    all_genres = [g for row in film_result.all() if row[0] for g in row[0]]

    genre_weights = {}
    if all_genres:
        counts = Counter(all_genres)
        max_cnt = max(counts.values())
        if max_cnt > 0:
            genre_weights = {
                g: (cnt / max_cnt) for g, cnt in counts.items() if (cnt / max_cnt) > 0.5
            }

    return avg_vector, genre_weights
    
@post("/films/recommend")
async def recommend_films(
    film_ids: list[UUID],
    db_session: AsyncSession,
    limit: int = 20,
) -> list[FilmSearchResponse]:

    if not film_ids:
        return []

    avg_vector, seed_genres = await _get_seed_genres_and_vector(film_ids, db_session)

    # Инициализация скоринга
    score_parts = []
    
    # 1. Скор по жанрам (теперь без жесткого фильтра)
    if seed_genres:
        sum_weights_expr = sum(
            [case((Film.genres.any(genre), weight), else_=0.0) for genre, weight in seed_genres.items()]
        )
        # Увеличиваем вес жанров, чтобы они лучше работали как "фильтр по смыслу"
        score_parts.append(sum_weights_expr * 0.4)

    # 2. Скор по векторам
    if avg_vector:
        cosine_similarity = 1.0 - Vector.vector.cosine_distance(avg_vector)
        score_parts.append(cosine_similarity * 0.6)

    # 3. Fallback: если вообще нет векторов и жанров, сортируем по дате (популярности)
    if not score_parts:
        final_score = Film.year_of_release # Просто возвращаем свежие
    else:
        final_score = sum(score_parts)

    # 4. Строим запрос БЕЗ жесткого .where(overlap)
    # Это гарантирует, что запрос всегда вернет фильмы, даже если жанры не совпали
    statement = (
        select(Film, final_score.label("score"))
        .join(Vector, Vector.file_id == Film.id)
        .where(Film.id.not_in(film_ids)) # Исключаем только те, что уже есть
        .order_by(desc("score"))
        .limit(limit)
    )

    result = await db_session.execute(statement)
    
    rows = result.all()
    
    # Если база пустая или фильтры исключили все, можно сделать еще один fallback
    # но обычно при такой логике что-то да найдется.
    
    return [
        FilmSearchResponse(
            id=row.Film.id,
            name=row.Film.name,
            description=row.Film.description,
            year_of_release=row.Film.year_of_release,
            image_path=row.Film.image_path,
            genres=row.Film.genres,
        )
        for row in rows
    ]