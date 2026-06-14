import requests
from api.models import ArtistGetResult
from db.models import ArtistRecord

HEADERS = {
    'X-Yandex-Music-Client': 'YandexMusicAndroid/24023621',
}
DEFAULT_TIMEOUT = 5


class _RequestsWrapper:
    def __init__(self, token: str, language: str = 'ru'):
        self.headers = {
            **HEADERS,
            'Authorization': f'OAuth {token}',
            'Accept-Language': language,
        }

    def get(self, url: str) -> dict:
        response = requests.get(
            url,
            headers=self.headers,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()
        return response.json()


BASE_URL = 'https://api.music.yandex.net'


def _parse_artist(artist_data: dict) -> ArtistGetResult:
    result = artist_data.get('result')

    _artist = result.get('artist')

    idx = _artist.get('id')
    is_available = _artist.get('available', False)
    name = _artist.get('name')

    genres = _artist.get('genres', [])
    countries = _artist.get('countries', [])

    _counts = _artist.get('counts')
    tracks_count = _counts.get('tracks', 0)

    likes_count = _artist.get('likesCount', 0)

    _ratings = _artist.get('ratings', {'day': 0, 'month': 0, 'week': 0})
    ratings_day = _ratings.get('day', 0)
    ratings_month = _ratings.get('month', 0)
    ratings_week = _ratings.get('week', 0)

    _stats = result.get('stats', {'last_month_listeners': 0, 'last_month_listeners_delta': 0})
    last_month_listeners = _stats.get('lastMonthListeners', 0)
    last_month_listeners_delta = _stats.get('lastMonthListenersDelta', 0)

    _similar_artists = result.get('similarArtists', [])
    similar_artist_ids = []

    for similar_artist in _similar_artists:
        similar_artist_idx = similar_artist.get('id')
        similar_artist_ids.append(similar_artist_idx)

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
    def __init__(self, token: str, language: str = 'ru'):
        self.requests = _RequestsWrapper(token, language)

    def get(self, artist_id: int) -> ArtistGetResult:
        url = f"{BASE_URL}/artists/{artist_id}/brief-info"
        data = self.requests.get(url)
        return _parse_artist(data)
