import aiohttp
import asyncio
from sentence_transformers import SentenceTransformer
from datetime import datetime
from src.database.table import Film, Vector
from src.database.session import Session
from src.core.config import config
from uuid import uuid7

TMBD_TOKEN = config.api.tmdb_token
NUM_PAGES_TO_FETCH = 5
MAX_CONCURRENT_REQUESTS = 5

HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json"
}

TMBD_GENRES_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

print("Neural network is loading...")
model = SentenceTransformer('intfloat/multilingual-e5-large')


async def fetch_movies(session: aiohttp.ClientSession, page: int = 1):
    url = f"https://api.themoviedb.org/3/movie/popular?language=uk-UA&page={page}"
    async with session.get(url, headers=HEADERS) as response:
        if response.status != 200:
            print(f"Failed to fetch page {page}: {response.status}.")
            return {}
        return await response.json()


async def download_image(session: aiohttp.ClientSession, poster_path: str) -> bytes | None:
    if not poster_path:
        return None
    url = f"https://image.tmdb.org/t/p/w500{poster_path}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            return None
    except Exception as e:
        print(f"Failed to load poster {poster_path}: {e}")
        return None


def get_vector(text: str) -> list[float]:
    if not text:
        text = "No description available."
    embedding = model.encode(f"passage: {text}")
    return embedding.tolist()


async def save_movie(semaphore: asyncio.Semaphore, session: aiohttp.ClientSession, db_session, movie_data: dict):    
    if not movie_data.get("release_date") or not movie_data.get("overview"):
        return
    
    title = movie_data.get("title", "Unknown")

    async with semaphore:
        print(f"Processing film {title}.")
        image_bytes = await download_image(session, movie_data.get("poster_path"))
        vector_data = await asyncio.to_thread(get_vector, movie_data["overview"])
        try:
            release_date = datetime.strptime(movie_data['release_date'], '%Y-%m-%d')
        except ValueError:
            release_date = datetime.now()

        genre_ids = movie_data.get("genre_ids", [])
        genres_list = [TMBD_GENRES_MAP[g_id] for g_id in genre_ids if g_id in TMBD_GENRES_MAP]
        if not genres_list:
            genres_list = ["Unknown"]

        film_id = uuid7()

        film = Film(
            id=film_id, name=movie_data['title'],
            description=movie_data['overview'],
            year_of_release = release_date, 
            genres=genres_list,
            image_data=image_bytes
        )

        film_vector = Vector(
            file_id=film_id, vector=vector_data,
            model="intfloat/multilingual-e5-large"
        )

        db_session.add(film)
        db_session.add(film_vector)


async def main():
    Session.setup(
        config.api.database.url.encoded_string(), echo=False
    )

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async for db_session in Session.session():
        async with aiohttp.ClientSession() as http_session:
            print(f"Fetching data. Number of pages: {NUM_PAGES_TO_FETCH}.")

            api_tasks = [fetch_movies(http_session, page) for page in range(1, NUM_PAGES_TO_FETCH+1)]
            pages_res = await asyncio.gather(*api_tasks)

            all_movies = []
            for data in pages_res:
                all_movies.extend(data.get("results", []))

            if not all_movies:
                print("No films found on these pages.")
                break
        
            print(f"Processing {len(all_movies)} movies.")
            pages_tasks = [save_movie(semaphore, http_session, db_session, movie) for movie in all_movies] 
            await asyncio.gather(*pages_tasks)

            print(f"Saving parsed movies to the database.")
            await db_session.commit()
        break

    await Session.dispose()
    print("Films have been successfully added to database.")


if __name__ == "__main__":
    asyncio.run(main())