import random
from datetime import timedelta

from config import CrawlerConfig
from crawler.api import ApiClient
from crawler.api import ArtistGetResult
from db import Repository
from crawler.utils.queue import Queue
from crawler.utils.rate_limiter import RateLimiter


class Crawler:
    def __init__(self, repository: Repository, config: CrawlerConfig):
        self.repository = repository
        self.refresh_interval = config.refresh_interval

        self.range_artist_id = config.range_artist_id

        self.queue = Queue(config.queue_config)
        self.api_client = ApiClient(config.api_client_config)
        self.rate_limiter = RateLimiter(config.rate_limiter)

    def _get_random_artist_id(self) -> int:
        return random.randint(self.range_artist_id.min, self.range_artist_id.max)

    def __iter__(self):
        return self

    def _next_artist_id(self) -> int:
        if self.queue:
            return self.queue.popleft()

        return _get_random_artist_id()

    def _is_actual(self, artist_id: int) -> bool:
        if not self.repository.artist_exists(artist_id):
            return False

        age = self.repository.get_record_age(artist_id)

        return age < timedelta(seconds=self.refresh_interval)

    def _save(self, result: ArtistGetResult):
        if self.repository.artist_exists(result.artist.id):
            self.repository.update_artist(result.artist)
        else:
            self.repository.add_artist(result.artist)

    def _get_artist(self, artist_id: int) -> list:
        if self._is_actual(artist_id):
            return []

        self.rate_limiter.wait()
        result = self.api_client.get(artist_id)
        self._save(result)

        return result.similar_artist_ids

    def _process_artist(self, artist_id: int):
        similar_artist_ids = self._get_artist(artist_id)

        self.queue.extend(similar_artist_ids)

    def __next__(self) -> (int, int):
        current_id = self._next_artist_id()
        self._process_artist(current_id)

        return current_id, len(self.queue)
