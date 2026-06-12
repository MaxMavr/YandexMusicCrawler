from collections import deque
import random

from api.artist import ArtistApiClient
from db.models import ArtistRecord


def get_random_artist_id(min_id=1, max_id=20_000_000):
    return random.randint(min_id, max_id)


class Crawler:
    def __init__(self, artist_api_client, seed_ids):
        self.artist_api_client = artist_api_client
        self.queue = deque(seed_ids)

    @classmethod
    def from_random(cls, count: int, artist_api_client):
        seed_ids = [
            get_random_artist_id()
            for _ in range(count)
        ]
        return cls(artist_api_client, seed_ids)

    @classmethod
    def from_list(cls, artist_ids: list[int], artist_api_client):
        return cls(artist_api_client, artist_ids)

    def __iter__(self):
        return self

    def __next__(self) -> ArtistRecord:
        print(self.queue)

        idx = self.queue.popleft() if self.queue else get_random_artist_id()

        try:
            result = self.artist_api_client.get(idx)
            self.queue.extend(result.similar_artist_ids)
            return result.artist
        except Exception as e:
            print('id:', idx, 'Exception:', e)
            return None