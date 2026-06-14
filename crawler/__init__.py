import random
from datetime import timedelta
from api.artist import ApiClient
from api.models import ArtistGetResult
from config import RANGE_ARTIST_ID, REFRESH_INTERVAL
from db import Repository, ArtistRecord
from utils.queue import Queue
from utils.rate_limiter import RateLimiter


def _get_random_artist_id() -> int:
    return random.randint(*RANGE_ARTIST_ID)


class Crawler:
    def __init__(self, api_client: ApiClient, repository: Repository, seed_ids: list[int], rate_limiter: RateLimiter):
        self.api_client = api_client
        self.repository = repository
        self.queue = Queue(seed_ids)
        self.rate_limiter = rate_limiter

    @classmethod
    def from_random(cls, count: int, api_client: ApiClient, repository: Repository, rate_limiter: RateLimiter):
        seed_ids = [
            _get_random_artist_id()
            for _ in range(count)
        ]
        return cls(api_client, repository, seed_ids, rate_limiter)

    @classmethod
    def from_list(cls, artist_ids: list[int], api_client: ApiClient, repository: Repository, rate_limiter: RateLimiter):
        return cls(api_client, repository, artist_ids, rate_limiter)

    def __iter__(self):
        return self

    def _next_artist_id(self) -> int:
        if self.queue:
            return self.queue.popleft()

        return _get_random_artist_id()

    def _is_actual(self, artist_id: int) -> bool:
        if not self.repository.exists(artist_id):
            return False

        age = self.repository.get_record_age(artist_id)

        return age < timedelta(seconds=REFRESH_INTERVAL)

    def _save(self, result: ArtistGetResult):
        if self.repository.exists(result.artist.id):
            self.repository.update(result.artist)
        else:
            self.repository.add(result.artist)

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
