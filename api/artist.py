from datetime import date
from api import Request
from api.models import ArtistGetResult
from db import ArtistRecord

BASE_URL = 'https://api.music.yandex.net'


def _parse(artist_data: dict) -> ArtistGetResult:
    result = artist_data.get('result')

    _stats = result.get('stats')
    last_month_listeners = _stats.get('lastMonthListeners')
    last_month_listeners_delta = _stats.get('lastMonthListenersDelta')

    _artist = result.get('artist')

    idx = _artist.get('id')
    available = _artist.get('available')
    name = _artist.get('name')
    init_date = _artist.get('initDate')
    init_timestamp = date.fromisoformat(init_date)

    genres = _artist.get('genres')
    countries = _artist.get('countries')

    _counts = _artist.get('counts')
    tracks_count = _counts.get('tracks')

    likes_count = _artist.get('likesCount')

    _ratings = _artist.get('ratings')
    ratings_day = _ratings.get('day')
    ratings_month = _ratings.get('month')
    ratings_week = _ratings.get('week')

    _similar_artists = result.get('similarArtists')
    similar_artist_ids = []

    for similar_artist in _similar_artists:
        similar_artist_idx = similar_artist.get('similarArtists')
        similar_artist_ids.append(similar_artist_idx)

    return ArtistGetResult(
        artist=ArtistRecord(
            last_month_listeners=last_month_listeners,
            last_month_listeners_delta=last_month_listeners_delta,
            id=idx,
            available=available,
            name=name,
            init_timestamp=init_timestamp,
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


class ArtistApiClient:
    def __init__(self, api: Request):
        self.api = api

    def get(self, artist_id: int) -> ArtistGetResult:
        url = f"{BASE_URL}/artists/{artist_id}/brief-info"
        data = self.api.get(url)
        return _parse(data)
