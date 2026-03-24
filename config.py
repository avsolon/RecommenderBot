import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# БД
DATABASE_PATH = os.getenv("DATABASE_PATH", "recommendations.db")

# Настройки прокси (если нужен)
#PROXY_URL = os.getenv("PROXY_URL", None)
