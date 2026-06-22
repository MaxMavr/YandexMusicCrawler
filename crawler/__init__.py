from random import randint
import threading
from typing import Literal, Optional

from config import CrawlerConfig
from crawler.api import ApiClient
from db import Repository
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

        self.debug_flag = config.debug_flag
        self.update_batch_size = config.update_batch_size
        self._update_batch: list[int] = []
        self.updated_count = 0

    async def run(self, strategy: Optional[Strategy] = None):
        if strategy is not None:
            self.strategy = strategy

        async with self.api_client, self.ids_pool:
            while not self.stop_event.is_set():
                current_id = await self._next_id()

                if current_id is None:
                    if self.debug_flag:
                        print('Crawler: Finished round')
                        break
                    continue

                try:
                    await self._process_artist(current_id)
                except Exception as e:
                    print(f'Crawler: Failed to process {current_id}: {e}')

                if self.debug_flag:
                    print(f'Crawler: id {current_id:<10}', end='')

                    match self.strategy:
                        case 'order':
                            print(f'| max id: {self.range_artist_id.max} | strategy: order')
                        case 'similar':
                            print(f'| pool: {len(self.ids_pool):<10} | strategy: similar')
                        case 'similar-random':
                            print(f'| pool: {len(self.ids_pool):<10} | strategy: similar-random')
                        case 'update':
                            print(
                                f'| updated: {self.updated_count:>10} | batch left: {len(self._update_batch):<6} | strategy: update')
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
                if not self._update_batch:
                    self._update_batch = self.repository.get_stale_artist_ids(
                        delta_time=self.refresh_interval,
                        limit=self.update_batch_size,
                    )

                    if not self._update_batch:
                        return None

                return self._update_batch.pop(0)

        raise ValueError(f'Crawler: Unknown strategy: {self.strategy}')

    def _is_actual_artist(self, artist_id: int) -> bool:
        if not self.repository.artist_exists(artist_id):
            return False

        age = self.repository.get_record_age(artist_id)

        return age < self.refresh_interval

    async def _process_artist(self, artist_id: int):
        if self.strategy != 'update' and self._is_actual_artist(artist_id):
            return

        await self.rate_limiter.wait()
        result = await self.api_client.get(artist_id)
        self.repository.upsert_artist(result.artist)
        self.updated_count += 1

        if self.strategy in ('similar', 'similar-random'):
            await self.ids_pool.update(result.similar_artist_ids)
