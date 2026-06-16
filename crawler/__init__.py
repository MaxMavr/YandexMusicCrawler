import random
import threading
from datetime import timedelta

from config import CrawlerConfig
from crawler.api import ApiClient
from crawler.api import ArtistGetResult
from db import Repository
from crawler.utils.pool import Pool
from crawler.utils.rate_limiter import RateLimiter


class Crawler:
    def __init__(self, repository: Repository, config: CrawlerConfig):
        self.repository = repository
        self.refresh_interval = config.refresh_interval

        self.range_artist_id = config.range_artist_id

        self.ids_pool = Pool(config.pool_config)
        self.api_client = ApiClient(config.api_client_config)
        self.rate_limiter = RateLimiter(config.rate_limiter)
        self.status_check_timeout = config.status_check_timeout

        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            if not self.repository.is_crawler_running():
                self.stop_event.wait(self.status_check_timeout)
                continue

            current_id = self._next_id()

            self._process_artist(current_id)

            print('id', current_id, 'len', len(self.ids_pool))

            if self.stop_event.is_set():
                break

        self.ids_pool.save()

    def stop(self):
        self.stop_event.set()

    def _get_random_id(self) -> int:
        return random.randint(self.range_artist_id.min, self.range_artist_id.max)

    def _next_id(self) -> int:
        if self.ids_pool:
            return self.ids_pool.next()

        return self._get_random_id()

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

        self.ids_pool.update(similar_artist_ids)
