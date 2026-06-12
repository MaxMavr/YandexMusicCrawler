from dataclasses import dataclass
from api import YandexRequest

BASE_URL = 'https://api.music.yandex.net'


@dataclass
class ArtistRecord:
    data: dict
    id: int
    name: str
    genre: str
    monthly_listeners: int
    country: str = "Unknown"
    is_active: bool = True


class ArtistService:
    def __init__(self, api: YandexRequest):
        self.api = api

    def get(self, artist_id: int) -> ArtistRecord:
        url = f"{BASE_URL}/artists/{artist_id}/brief-info"

        data = self.api.get(url)

        return ArtistRecord(
            data=data,
            id=0,
            name="Unknown",
            genre="Unknown",
            monthly_listeners=0,
        )