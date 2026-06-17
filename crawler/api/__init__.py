import requests

from config import ApiClientConfig
from crawler.api.models import ArtistGetResult
from db.models import ArtistRecord
from typing import Any

HEADERS = {
    'X-Yandex-Music-Client': 'YandexMusicAndroid/24023621'
}


def _parse_artist(artist_data: dict[str, Any]) -> ArtistGetResult:
    result = artist_data.get("result")
    if not result:
        raise ValueError("Неверный ответ API: отсутствует результат")

    _artist = result.get('artist')
    if not _artist:
        raise ValueError("Неверный ответ API: отсутствует artist")

    idx = _artist.get('id')
    name = _artist.get('name')
    is_available = _artist.get('available', False)

    genres = _artist.get('genres', [])
    countries = _artist.get('countries', [])

    _counts = _artist.get('counts', {})
    tracks_count = _counts.get('tracks', 0)

    likes_count = _artist.get('likesCount', 0)

    _ratings = _artist.get('ratings', {})
    ratings_day = _ratings.get('day', 0)
    ratings_month = _ratings.get('month', 0)
    ratings_week = _ratings.get('week', 0)

    _stats = result.get('stats', {})
    last_month_listeners = _stats.get('lastMonthListeners', 0)
    last_month_listeners_delta = _stats.get('lastMonthListenersDelta', 0)

    _similar_artists = result.get('similarArtists', [])
    similar_artist_ids = [
        artist.get("id")
        for artist in _similar_artists
        if "id" in artist
    ]

    return ArtistGetResult(
        artist=ArtistRecord(
            last_month_listeners=last_month_listeners,
            last_month_listeners_delta=last_month_listeners_delta,
            id=idx,
            is_available=is_available,
            name=name,
            genres=genres,
            countries=countries,
            tracks_count=tracks_count,
            likes_count=likes_count,
            ratings_day=ratings_day,
            ratings_month=ratings_month,
            ratings_week=ratings_week
        ),
        similar_artist_ids=similar_artist_ids
    )


class ApiClient:
    def __init__(self, config: ApiClientConfig):
        self.requests = _RequestsWrapper(config)

    def get(self, artist_id: int) -> ArtistGetResult:
        url = f"{BASE_URL}/artists/{artist_id}/brief-info"
        data = self.requests.get(url)
        return _parse_artist(data)
