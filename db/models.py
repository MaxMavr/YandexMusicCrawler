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


@dataclass
class PaginationResult:
    """Результат пагинации"""
    items: list[ArtistRecord]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool