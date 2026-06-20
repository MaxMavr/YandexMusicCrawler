from random import randint
import threading
from datetime import timedelta

from config import CrawlerConfig
from crawler.api import ApiClient
from crawler.api import ArtistGetResult
from db import Repository
from crawler.utils.pool import Pool
from crawler.utils.rate_limiter import RateLimiter

# from typing import Literal
# Literal['random', 'order', 'similar']


class Crawler:
    def __init__(self, repository: Repository, config: CrawlerConfig):
        self.repository = repository
        self.refresh_interval = config.refresh_interval

        self.range_artist_id = config.range_artist_id

        self.api_client = ApiClient(config.api_client_config)
        self.rate_limiter = RateLimiter(config.rate_limiter)

        self.strategy = config.strategy
        self.ids_pool = Pool(config.pool_config)

        self.stop_event = threading.Event()

    async def run(self):
        async with self.api_client, self.ids_pool:
            while not self.stop_event.is_set():
                current_id = await self._next_id()

                try:
                    await self._process_artist(current_id)
                except Exception as e:
                    print(f'Failed to process {current_id}: {e}')
                print(f'id {current_id:<10} len {len(self.ids_pool):<10}')
            await self.ids_pool.save()

    def stop(self):
        self.stop_event.set()

    def _get_random_id(self) -> int:
        return randint(self.range_artist_id.min, self.range_artist_id.max)

    async def _next_id(self) -> int:
        if self.ids_pool:
            return await self.ids_pool.next()

        return self._get_random_id()

    def _is_actual_artist(self, artist_id: int) -> bool:
        if not self.repository.artist_exists(artist_id):
            return False

        age = self.repository.get_record_age(artist_id)

        return age < timedelta(seconds=self.refresh_interval)

    def _save_artist(self, result: ArtistGetResult):
        if self.repository.artist_exists(result.artist.id):
            self.repository.update_artist(result.artist)
        else:
            self.repository.add_artist(result.artist)

    async def _process_artist(self, artist_id: int):
        if self._is_actual_artist(artist_id):
            return

        await self.rate_limiter.wait()
        result = await self.api_client.get(artist_id)
        self._save_artist(result)

        similar_artist_ids = result.similar_artist_ids
        await self.ids_pool.update(similar_artist_ids)
