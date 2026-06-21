from random import randint
import threading
from datetime import timedelta
from typing import Literal, Optional

from config import CrawlerConfig
from crawler.api import ApiClient
from db import Repository, ArtistRecord
from crawler.utils.pool import Pool
from crawler.utils.rate_limiter import RateLimiter

Strategy = Literal['order', 'update', 'similar', 'similar-random', 'random']


class Crawler:
    def __init__(self, repository: Repository, config: CrawlerConfig):
        self.repository = repository
        self.refresh_interval = config.refresh_interval

        self.range_artist_id = config.range_artist_id

        self.api_client = ApiClient(config.api_client_config)
        self.rate_limiter = RateLimiter(config.rate_limiter)

        self.strategy = config.strategy
        self.stop_event = threading.Event()

        self.ids_pool = Pool(config.pool_config)
        self.current_order_id = self.range_artist_id.min
        self.current_update_index = 0
        self.max_update_index = self.repository.get_artists_count()

    async def run(self, strategy: Optional[Strategy] = None):
        if strategy is not None:
            self.strategy = strategy

        async with self.api_client, self.ids_pool:
            while not self.stop_event.is_set():
                current_id = await self._next_id()

                if current_id is None:
                    print('Crawler: Finished round')
                    break

                try:
                    await self._process_artist(current_id)
                except Exception as e:
                    print(f'Crawler: Failed to process {current_id}: {e}')
                print(f'Crawler: id {current_id:<10} len {len(self.ids_pool):<10}')
            await self.ids_pool.save()

    def stop(self):
        self.stop_event.set()

    def _get_random_id(self) -> int:
        return randint(self.range_artist_id.min, self.range_artist_id.max)

    async def _next_id(self) -> int | None:
        match self.strategy:
            case 'random':
                return self._get_random_id()

            case 'order':
                if self.current_order_id > self.range_artist_id.max:
                    return None

                current = self.current_order_id
                self.current_order_id += 1
                return current

            case 'similar':
                if self.ids_pool:
                    return await self.ids_pool.next()
                return None

            case 'similar-random':
                if self.ids_pool:
                    return await self.ids_pool.next()
                return self._get_random_id()

            case 'update':
                if self.current_update_index >= self.max_update_index:
                    return None

                current = self.current_update_index
                self.current_update_index += 1
                return self.repository.get_artist_at(index=current, sort_by="id").id

        raise ValueError(f'Crawler: Unknown strategy: {self.strategy}')

    def _is_actual_artist(self, artist_id: int) -> bool:
        if not self.repository.artist_exists(artist_id):
            return False

        age = self.repository.get_record_age(artist_id)

        return age < self.refresh_interval

    def _save_artist(self, artist: ArtistRecord):
        if self.repository.artist_exists(artist.id):
            self.repository.update_artist(artist)
        else:
            self.repository.add_artist(artist)

    async def _process_artist(self, artist_id: int):
        if self._is_actual_artist(artist_id):
            return

        await self.rate_limiter.wait()
        result = await self.api_client.get(artist_id)
        self._save_artist(result.artist)

        if self.strategy in ('similar', 'similar-random'):
            await self.ids_pool.update(result.similar_artist_ids)
