from os import getenv
from dotenv import load_dotenv

load_dotenv()

PG_DSN = getenv("PG_DSN")
PG_USER = getenv("PG_USER", "app_user")
PG_PASSWORD = getenv("PG_PASSWORD", "password")
PG_HOST = getenv("PG_HOST", "127.0.0.1")
PG_PORT = getenv("PG_PORT", 5431)
PG_DB = getenv("PG_DB", "app_db")
TOKEN_TTL = getenv("TOKEN_TTL")
PG_DSN = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
