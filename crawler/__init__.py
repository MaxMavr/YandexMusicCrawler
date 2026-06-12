from collections import deque
import random

from api.artist import ArtistApiClient
from db import ArtistRecord


def get_random_artist_id(min_id=1, max_id=20_000_000):
    return random.randint(min_id, max_id)


class Crawler:
    def __init__(self, count: int, artist_api_client: ArtistApiClient):
        self.artist_api_client = artist_api_client
        self.queue = deque()
        for _ in range(count):
            artist_id = get_random_artist_id()
            self.queue.append(artist_id)

    def __iter__(self):
        return self

    def __next__(self) -> ArtistRecord:
        idx = self.queue.popleft() if self.queue else get_random_artist_id()
        result = self.artist_api_client.get(idx)

        self.queue.extend(result.similar_artist_ids)

        return result.artist
