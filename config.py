from collections import namedtuple
from dataclasses import dataclass
from datetime import timedelta
from os import getenv
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

TEMP_PATH = Path("temp")

load_dotenv(find_dotenv())


@dataclass
class ApiClientConfig:
    token: str = getenv("YANDEX_TOKEN")
    language: str = "ru"
    timeout: int = 15
    base_url: str = 'https://api.music.yandex.net'


@dataclass
class PoolConfig:
    file: Path = TEMP_PATH / "queue.json"
    save_frequency: int = 1000  # сохраняем каждый 1000 шагов


Range = namedtuple('Range', ['min', 'max'])


@dataclass
class CrawlerConfig:
    api_client_config: ApiClientConfig
    pool_config: PoolConfig
    rate_limiter: float = 3  # 3 запроса/сек
    refresh_interval: timedelta = timedelta(days=2, hours=0)  # 30 * 24 * 60 * 60 30 дней
    range_artist_id = Range(min=1, max=20_000_000)
    debug_flag: bool = True
    update_batch_size: int = 500
    strategy = 'similar'  # 'order', 'update', 'similar', 'similar-random', 'random'


@dataclass
class RepositoryConfig:
    database: str = "music"
    password: str = getenv("POSTGRESQL_PASSWORD")
    user: str = "postgres"
    host: str = "localhost"
    port: int = 5432


CRAWLER_CONFIG = CrawlerConfig(
    api_client_config=ApiClientConfig(),
    pool_config=PoolConfig()
)

REPOSITORY_CONFIG = RepositoryConfig()

TEMP_PATH.mkdir(parents=True, exist_ok=True)
