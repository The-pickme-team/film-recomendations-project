import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

import aiofiles
import aiohttp
import uvloop
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database.table import Film, Vector

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dbname"
)

IMAGES_DIR = Path(__file__).parent.parent / "images"
FILMS_TARGET_COUNT = int(os.getenv("FILMS_TARGET_COUNT", "1000"))


def resolve_films_file() -> Path:
    candidates = []

    films_file_env = os.getenv("FILMS_FILE")
    if films_file_env:
        candidates.append(Path(films_file_env))

    candidates.extend(
        [
            Path.cwd() / "films.txt",
            Path("/app/films.txt"),
            Path(__file__).resolve().parents[2] / "films.txt",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


FILMS_FILE = resolve_films_file()

# Кешування моделі
model = SentenceTransformer("BAAI/bge-m3", device="cpu")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def get_tmdb_api_key() -> str:
    if TMDB_API_KEY is None:
        raise RuntimeError("TMDB_API_KEY не встановлено")
    return TMDB_API_KEY


def encode_texts_sync(texts: list[str]) -> list[list[float]]:
    """Синхронна функція для генерації ембедингів."""
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def normalize_title(title: str) -> str:
    return " ".join(re.sub(r"[^\w\s]+", " ", title.lower(), flags=re.UNICODE).split())


def title_matches(query: str, candidate: str) -> bool:
    query_normalized = normalize_title(query)
    candidate_normalized = normalize_title(candidate)
    return (
        query_normalized == candidate_normalized
        or query_normalized in candidate_normalized
        or candidate_normalized in query_normalized
    )


def load_film_titles() -> list[str]:
    if not FILMS_FILE.exists():
        return []

    return [
        line.strip()
        for line in FILMS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_film_titles_set() -> set[str]:
    return set(load_film_titles())


async def append_movies_to_films_file(movies: list[dict]) -> None:
    titles_to_add = [movie["name"].strip() for movie in movies if movie.get("name")]
    if not titles_to_add:
        return

    existing_titles = load_film_titles_set()
    unique_titles = [title for title in titles_to_add if title not in existing_titles]
    if not unique_titles:
        return

    FILMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_existed = FILMS_FILE.exists()
    file_had_content = file_existed and FILMS_FILE.stat().st_size > 0

    async with aiofiles.open(FILMS_FILE, mode="a", encoding="utf-8") as file:
        if file_had_content:
            await file.write("\n")
        await file.write("\n".join(unique_titles))
        await file.write("\n")


async def search_movie_by_title(
    session: aiohttp.ClientSession,
    title: str,
    genre_mapping: dict[int, str],
    language: str,
) -> dict | None:
    url = f"{BASE_URL}/search/movie"
    params: dict[str, str | int] = {
        "api_key": get_tmdb_api_key(),
        "language": language,
        "query": title,
        "include_adult": "false",
        "page": 1,
    }

    async with session.get(url, params=params) as response:
        response.raise_for_status()
        data = await response.json()

    results = data.get("results", [])
    if not results:
        return None

    best_item = None
    for item in results:
        candidate_title = item.get("title") or item.get("original_title") or ""
        if not candidate_title:
            continue

        if title_matches(title, candidate_title):
            best_item = item
            break

        if best_item is None:
            best_item = item

    if best_item is None:
        return None

    candidate_title = best_item.get("title") or best_item.get("original_title")
    overview = best_item.get("overview")
    release_date_raw = best_item.get("release_date")

    if not candidate_title or not overview or not release_date_raw:
        return None

    try:
        release_date = datetime.strptime(release_date_raw, "%Y-%m-%d")
    except ValueError:
        return None

    genre_names = [
        genre_mapping[g_id]
        for g_id in best_item.get("genre_ids", [])
        if g_id in genre_mapping
    ]

    poster_path = best_item.get("poster_path")
    local_image_path = await download_image(session, poster_path)

    return {
        "name": candidate_title,
        "description": overview,
        "year_of_release": release_date,
        "genres": genre_names,
        "image_path": f"/media/{Path(local_image_path).name}" if local_image_path else "",
    }


async def get_existing_film_names() -> set[str]:
    """Отримує список назв усіх фільмів, що вже є в базі, щоб уникати дублікатів."""
    async with async_session() as db_session:
        result = await db_session.execute(select(Film.name))
        # Повертаємо множину (set) для миттєвого пошуку O(1)
        return {row[0] for row in result.all()}


async def get_genre_mapping(
    session: aiohttp.ClientSession, language: str
) -> dict[int, str]:
    url = f"{BASE_URL}/genre/movie/list"
    params: dict[str, str] = {"api_key": get_tmdb_api_key(), "language": language}

    async with session.get(url, params=params) as response:
        response.raise_for_status()
        data = await response.json()
        return {genre["id"]: genre["name"] for genre in data.get("genres", [])}


async def download_image(session: aiohttp.ClientSession, poster_path: str) -> str:
    if not poster_path:
        return ""

    filename = poster_path.lstrip("/")
    local_path = IMAGES_DIR / filename
    url = f"{IMAGE_BASE_URL}{poster_path}"

    if local_path.exists():
        return str(local_path)

    try:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, mode="wb") as f:
                    async for chunk in response.content.iter_chunked(1024):
                        await f.write(chunk)
                return str(local_path)
    except Exception as e:
        print(f"Не вдалося завантажити зображення {url}: {e}")

    return ""


async def collect_movies_from_films_file(
    session: aiohttp.ClientSession,
    genre_mapping: dict[int, str],
    existing_names: set[str],
) -> list[dict]:
    titles = load_film_titles()
    movies_ready = []
    search_languages = ["en-US", "uk-UA", "ru-RU"]

    print(f"Починаємо обробку {len(titles)} фільмів із films.txt...")

    for title in titles:
        movie = None
        for language in search_languages:
            movie = await search_movie_by_title(session, title, genre_mapping, language)
            if movie:
                break

        if movie is None:
            print(f"⚠️ Не вдалося знайти фільм у TMDB: {title}")
            continue

        if movie["name"] in existing_names:
            print(f"↩️ Пропускаємо вже наявний фільм: {movie['name']}")
            continue

        movies_ready.append(movie)
        existing_names.add(movie["name"])
        print(f"✅ Знайдено та підготовлено: {movie['name']}")

    return movies_ready


async def collect_unique_movies(
    session: aiohttp.ClientSession,
    genre_mapping: dict,
    existing_names: set[str],
    language: str = "en-US",
    target_count: int = 1000,
) -> list[dict]:
    """Збирає рівно target_count НОВИХ фільмів, гортаючи сторінки TMDB."""
    movies_ready = []
    page = 1
    processed_tmdb_ids = set()  # Щоб уникати дублікатів всередині одного запуску

    print(f"Починаємо пошук {target_count} нових фільмів для мови {language}...")

    while len(movies_ready) < target_count:
        url = f"{BASE_URL}/movie/popular"
        params: dict[str, str | int] = {
            "api_key": get_tmdb_api_key(),
            "language": language,
            "page": page,
        }

        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

        results = data.get("results", [])
        if not results:
            print("❌ TMDB повернув порожню сторінку. Більше фільмів немає.")
            break

        temp_movies = []
        image_tasks = []

        for item in results:
            tmdb_id = item.get("id")
            title = item.get("title")

            # Пропускаємо, якщо вже обробили цей ID в цьому циклі
            if tmdb_id in processed_tmdb_ids:
                continue

            # Пропускаємо, якщо фільм з такою назвою вже є в Базі Даних
            if title in existing_names:
                continue

            if not item.get("overview") or not item.get("release_date"):
                continue

            try:
                release_date = datetime.strptime(item["release_date"], "%Y-%m-%d")
            except ValueError:
                continue

            genre_names = [
                genre_mapping[g_id]
                for g_id in item.get("genre_ids", [])
                if g_id in genre_mapping
            ]
            poster_path = item.get("poster_path")

            processed_tmdb_ids.add(tmdb_id)

            task = asyncio.create_task(download_image(session, poster_path))
            image_tasks.append(task)

            temp_movies.append(
                {
                    "name": title,
                    "description": item["overview"],
                    "year_of_release": release_date,
                    "genres": genre_names,
                }
            )

            # Перевіряємо, чи не досягли ми ліміту прямо під час збору сторінки
            if len(movies_ready) + len(temp_movies) >= target_count:
                break

        # Чекаємо завантаження картинок тільки для відібраних нових фільмів
        downloaded_paths = await asyncio.gather(*image_tasks)

        for movie, local_img_path in zip(temp_movies, downloaded_paths):
            filename = Path(local_img_path).name
            movie["image_path"] = f"/media/{filename}" if filename else ""
            movies_ready.append(movie)

        print(
            f"[{language}] Зібрано {len(movies_ready)} / {target_count} нових фільмів (Оброблено сторінку {page})"
        )
        page += 1

    return movies_ready


async def process_and_save_movies(movies: list[dict]):
    """Генерує вектори та зберігає фільми у БД партіями (щоб не перевантажити RAM)."""
    if not movies:
        return

    BATCH_SIZE = 100

    for i in range(0, len(movies), BATCH_SIZE):
        batch = movies[i : i + BATCH_SIZE]
        texts_to_encode = []

        for m in batch:
            genres_str = ", ".join(m["genres"])
            context_text = (
                f"Назва: {m['name']}. Жанри: {genres_str}. Опис: {m['description']}"
            )
            texts_to_encode.append(context_text)

        print(
            f"Генеруємо вектори для партії {i + 1}-{i + len(batch)} із {len(movies)}..."
        )
        vectors = await asyncio.to_thread(encode_texts_sync, texts_to_encode)

        async with async_session() as db_session:
            for movie_data, vector_data in zip(batch, vectors):
                film_obj = Film(
                    name=movie_data["name"],
                    description=movie_data["description"],
                    year_of_release=movie_data["year_of_release"],
                    image_path=movie_data["image_path"],
                    genres=movie_data["genres"],
                )

                film_obj.vector = Vector(vector=vector_data, model="BAAI/bge-m3")
                db_session.add(film_obj)

            await db_session.commit()
            print("✅ Успішно додано партію до БД.")


async def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("Зчитуємо вже наявні фільми з бази даних...")
    existing_names = await get_existing_film_names()
    existing_count = len(existing_names)
    print(f"У базі вже є {existing_count} унікальних назв.")

    if existing_count >= FILMS_TARGET_COUNT:
        print(
            f"База вже містить {existing_count} фільмів, ціль {FILMS_TARGET_COUNT} досягнута."
        )
        return

    async with aiohttp.ClientSession() as session:
        print("Завантажуємо мапу жанрів...")
        genres_map = await get_genre_mapping(session, "en-US")

        seed_movies = await collect_movies_from_films_file(
            session=session,
            genre_mapping=genres_map,
            existing_names=existing_names,
        )

        if seed_movies:
            await process_and_save_movies(seed_movies)

        current_count = existing_count + len(seed_movies)
        if current_count < FILMS_TARGET_COUNT:
            missing_count = FILMS_TARGET_COUNT - current_count
            print(f"Догружаємо ще {missing_count} фільмів до цілі {FILMS_TARGET_COUNT}...")
            generated_movies = await collect_unique_movies(
                session=session,
                genre_mapping=genres_map,
                existing_names=existing_names,
                target_count=missing_count,
            )

            if generated_movies:
                await process_and_save_movies(generated_movies)
                await append_movies_to_films_file(generated_movies)
            else:
                print("Не вдалося добрати додаткові фільми до цільового ліміту.")

        if not seed_movies and existing_count < FILMS_TARGET_COUNT:
            print("Нових фільмів із films.txt не знайдено.")


if __name__ == "__main__":
    uvloop.run(main())
