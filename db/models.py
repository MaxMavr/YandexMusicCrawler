from dataclasses import dataclass


@dataclass
class ArtistRecord:
    last_month_listeners: int
    last_month_listeners_delta: int

    id: int
    is_available: bool
    name: str

    genres: list[str]
    countries: list[str]

    tracks_count: int
    likes_count: int

    ratings_day: int
    ratings_month: int
    ratings_week: int

    is_listened: bool = False

    def to_dict(self):
        return {
            'last_month_listeners': self.last_month_listeners,
            'last_month_listeners_delta': self.last_month_listeners_delta,
            'id': self.id,
            'is_available': self.is_available,
            'name': self.name,
            'genres': self.genres,
            'countries': self.countries,
            'tracks_count': self.tracks_count,
            'likes_count': self.likes_count,
            'ratings_day': self.ratings_day,
            'ratings_month': self.ratings_month,
            'ratings_week': self.ratings_week,
            'is_listened': self.is_listened
        }


@dataclass
class ArtistsPage:
    artist_records: list[ArtistRecord]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    def to_dict(self):
        return {
            'artists': [ar.to_dict() for ar in self.artist_records],
            'total': self.total,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev
        }
