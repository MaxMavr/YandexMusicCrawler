from collections import namedtuple
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

TEMP_PATH = Path("temp")

load_dotenv(find_dotenv())


@dataclass
class ApiClientConfig:
    token: str
    language: str = "ru"
    timeout: int = 15


@dataclass
class QueueConfig:
    queue_file: Path
    save_frequency: int = 100  # сохраняем каждый 100 шагов


Range = namedtuple('Range', ['min', 'max'])


@dataclass
class CrawlerConfig:
    api_client_config: ApiClientConfig
    queue_config: QueueConfig
    rate_limiter: float = 3  # 3 запроса/сек
    refresh_interval = 30 * 24 * 60 * 60  # 30 дней
    range_artist_id = Range(min=1, max=20_000_000)
    status_check_timeout = 5  # 5 сек


@dataclass
class RepositoryConfig:
    database: str
    password: str
    user: str = "postgres"
    host: str = "localhost"
    port: int = 5432


API_CLIENT_CONFIG = ApiClientConfig(
    token=getenv("YANDEX_TOKEN"),
)

QUEUE_CONFIG = QueueConfig(
    queue_file=TEMP_PATH / "queue.json",
)

CRAWLER_CONFIG = CrawlerConfig(
    api_client_config=API_CLIENT_CONFIG,
    queue_config=QUEUE_CONFIG,
)

REPOSITORY_CONFIG = RepositoryConfig(
    database="music",
    password=getenv("POSTGRESQL_PASSWORD"),
)

TEMP_PATH.mkdir(parents=True, exist_ok=True)
