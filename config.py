import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY = os.getenv("PROXY_URL")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/recommender"
)

BOT_USERNAME = os.getenv("BOT_USERNAME", "MyRecommenderBot")

CATEGORIES = {
    "films": "Фильмы",
    "books": "Книги",
    "series": "Сериалы",
    "music": "Музыка",
    "food": "Еда",
    "goods": "Товары",
    "games": "Игры",
    "places": "Места",
    "other": "Другое"
}

DEFAULT_PAGE_SIZE = 10

RATING_SCORES = [1, 2, 3, 4, 5]
