import asyncio
import os
from datetime import datetime
from pathlib import Path

import aiofiles
import aiohttp
import uvloop
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database.teble import Film, Vector

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dbname"
)

IMAGES_DIR = Path(__file__).parent.parent / "images"

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


async def collect_unique_movies(
    session: aiohttp.ClientSession,
    genre_mapping: dict,
    existing_names: set[str],
    language: str = "en-US",
    target_count: int = 1000
) -> list[dict]:
    """Збирає рівно target_count НОВИХ фільмів, гортаючи сторінки TMDB."""
    movies_ready = []
    page = 1
    processed_tmdb_ids = set() # Щоб уникати дублікатів всередині одного запуску

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

        print(f"[{language}] Зібрано {len(movies_ready)} / {target_count} нових фільмів (Оброблено сторінку {page})")
        page += 1

    return movies_ready


async def process_and_save_movies(movies: list[dict]):
    """Генерує вектори та зберігає фільми у БД партіями (щоб не перевантажити RAM)."""
    if not movies:
        return

    BATCH_SIZE = 1000

    for i in range(0, len(movies), BATCH_SIZE):
        batch = movies[i : i + BATCH_SIZE]
        texts_to_encode = []
        
        for m in batch:
            genres_str = ", ".join(m["genres"])
            context_text = f"Назва: {m['name']}. Жанри: {genres_str}. Опис: {m['description']}"
            texts_to_encode.append(context_text)

        print(f"Генеруємо вектори для партії {i + 1}-{i + len(batch)} із {len(movies)}...")
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
    TARGET_MOVIES_PER_LANGUAGE = 1000

    print("Зчитуємо вже наявні фільми з бази даних...")
    existing_names = await get_existing_film_names()
    print(f"У базі вже є {len(existing_names)} унікальних назв.")

    async with aiohttp.ClientSession() as session:
        for language in ["en-US"]:
            print(f"\n=== Обробка мови: {language} ===")
            print("Завантажуємо мапу жанрів...")
            genres_map = await get_genre_mapping(session, language)

            # Збираємо рівно потрібну кількість НОВИХ фільмів
            new_movies = await collect_unique_movies(
                session=session,
                genre_mapping=genres_map,
                existing_names=existing_names,
                language=language,
                target_count=TARGET_MOVIES_PER_LANGUAGE
            )

            if new_movies:
                await process_and_save_movies(new_movies)
                # Додаємо щойно збережені фільми до списку "існуючих", 
                # щоб наступна мова не дублювала їх, якщо назви співпадають.
                for m in new_movies:
                    existing_names.add(m["name"])
            else:
                print(f"Для мови {language} нових фільмів не знайдено.")

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())