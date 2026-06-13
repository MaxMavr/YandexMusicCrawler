from os import getenv
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

TEMP_PATH = Path("temp")
QUEUE_FILE = TEMP_PATH / "queue.json"

API_RATE = 3  # 3 запроса/сек
REFRESH_INTERVAL = 30 * 24 * 60 * 60  # 30 дней


RANGE_ARTIST_ID = (1, 20_000_000)



load_dotenv(find_dotenv())
YANDEX_TOKEN = getenv("YANDEX_TOKEN")
POSTGRESQL_PASSWORD = getenv("POSTGRESQL_PASSWORD")

TEMP_PATH.mkdir(parents=True, exist_ok=True)
