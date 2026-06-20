import aiohttp

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
    ratings_month = _ratings.get('month', 0)

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
            ratings_month=ratings_month,
        ),
        similar_artist_ids=similar_artist_ids
    )


class ApiClient:
    def __init__(self, config: ApiClientConfig):
        self.headers = {
            **HEADERS,
            'Authorization': f'OAuth {config.token}',
            'Accept-Language': config.language,
        }
        self.timeout = config.timeout
        self.base_url = config.base_url
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def get(self, artist_id: int) -> ArtistGetResult:
        if not self._session:
            raise RuntimeError("Сессия не инициализирована. Используйте 'async with'")

        url = f"{self.base_url}/artists/{artist_id}/brief-info"

        async with self._session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return _parse_artist(data)
