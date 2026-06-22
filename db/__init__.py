from datetime import datetime, timedelta
from typing import Optional

import psycopg
from psycopg import Cursor
from psycopg.rows import dict_row

from config import RepositoryConfig
from db.models import ArtistRecord, ArtistsPage

VALID_SORT_FIELDS = [
    "id", "name", "last_month_listeners", "last_month_listeners_delta",
    "tracks_count", "likes_count", "ratings_month",
    "is_available", "is_listened"
]


def _update_artist_relations(cur: Cursor, artist_id: int, genres: list[str], countries: list[str]) -> None:
    unique_genres = list(set(genres)) if genres else []
    unique_countries = list(set(countries)) if countries else []

    if unique_genres:
        cur.executemany(
            "INSERT INTO genres (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
            [(g,) for g in unique_genres]
        )

        cur.execute("""
            INSERT INTO artist_genres (artist_id, genre_id)
            SELECT %s, id FROM genres WHERE name = ANY(%s)
            ON CONFLICT DO NOTHING
        """, (artist_id, unique_genres))

    if unique_countries:
        cur.executemany(
            "INSERT INTO countries (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
            [(c,) for c in unique_countries]
        )

        cur.execute("""
            INSERT INTO artist_countries (artist_id, country_id)
            SELECT %s, id FROM countries WHERE name = ANY(%s)
            ON CONFLICT DO NOTHING
        """, (artist_id, unique_countries))


FILTER_MAP = {
    "is_available": ("a.is_available = %s", bool),
    "is_listened": ("a.is_listened = %s", bool),
    "min_listeners": ("a.last_month_listeners >= %s", int),
    "max_listeners": ("a.last_month_listeners <= %s", int),
    "min_listeners_delta": ("a.last_month_listeners_delta >= %s", int),
    "max_listeners_delta": ("a.last_month_listeners_delta <= %s", int),
    "min_likes": ("a.likes_count >= %s", int),
    "max_likes": ("a.likes_count <= %s", int),
    "min_tracks": ("a.tracks_count >= %s", int),
    "max_tracks": ("a.tracks_count <= %s", int),
    "min_ratings_month": ("a.ratings_month >= %s", int),
    "max_ratings_month": ("a.ratings_month <= %s", int),
}


def _build_artists_filters(filters: Optional[dict] = None) -> tuple[str, str, list]:
    base_query = """
        FROM artists a
        LEFT JOIN artist_genres ag ON a.id = ag.artist_id
        LEFT JOIN genres g ON ag.genre_id = g.id
        LEFT JOIN artist_countries ac ON a.id = ac.artist_id
        LEFT JOIN countries c ON ac.country_id = c.id
    """

    where_conditions = []
    params = []

    if filters:
        for key, (condition, expected_type) in FILTER_MAP.items():
            value = filters.get(key)
            if isinstance(value, expected_type):
                where_conditions.append(condition)
                params.append(value)

        if "name_contains" in filters:
            if isinstance(filters["name_contains"], str):
                where_conditions.append("a.name ILIKE %s")
                params.append(f"%{filters['name_contains']}%")

        if "genres" in filters:
            genres_list = filters["genres"]

            if (isinstance(genres_list, list)
                    and genres_list
                    and all(isinstance(g, str) for g in genres_list)):
                where_conditions.append("g.name = ANY(%s)")
                params.append(genres_list)

        if "countries" in filters:
            countries_list = filters["countries"]

            if (isinstance(countries_list, list)
                    and countries_list
                    and all(isinstance(c, str) for c in countries_list)):
                where_conditions.append("c.name = ANY(%s)")
                params.append(countries_list)

    where_clause = ""

    if where_conditions:
        where_clause = " WHERE " + " AND ".join(where_conditions)

    return base_query, where_clause, params


class Repository:
    def __init__(self, config: RepositoryConfig):
        self._dsn = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
        self._create_tables()

    def _connect(self):
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def _create_tables(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS artists (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        is_available BOOLEAN NOT NULL,

                        cover_uri TEXT NULL,

                        last_month_listeners INTEGER NOT NULL,
                        last_month_listeners_delta INTEGER NOT NULL,

                        tracks_count INTEGER NOT NULL,
                        likes_count INTEGER NOT NULL,
                        ratings_month INTEGER NOT NULL,

                        date_recording TIMESTAMP NOT NULL,

                        is_listened BOOLEAN NOT NULL
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS genres (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS countries (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS artist_genres (
                        artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
                        genre_id INTEGER REFERENCES genres(id) ON DELETE CASCADE,

                        PRIMARY KEY (artist_id, genre_id)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS artist_countries (
                        artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
                        country_id INTEGER REFERENCES countries(id) ON DELETE CASCADE,

                        PRIMARY KEY (artist_id, country_id)
                    );
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_date_recording
                    ON artists(date_recording);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_name
                    ON artists(name);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_listeners
                    ON artists(last_month_listeners);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_likes
                    ON artists(likes_count);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_tracks
                    ON artists(tracks_count);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_ratings
                    ON artists(ratings_month);
                """)

                cur.execute("""
                    CREATE EXTENSION IF NOT EXISTS pg_trgm;
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artists_name_trgm
                    ON artists USING gin (name gin_trgm_ops);
                """)
            conn.commit()

    def upsert_artist(self, artist: ArtistRecord) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO artists (
                        id,
                        date_recording,
                        last_month_listeners,
                        last_month_listeners_delta,
                        is_available,
                        name,
                        tracks_count,
                        likes_count,
                        ratings_month,
                        cover_uri,
                        is_listened
                    )
                    VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        date_recording = NOW(),
                        last_month_listeners = EXCLUDED.last_month_listeners,
                        last_month_listeners_delta = EXCLUDED.last_month_listeners_delta,
                        is_available = EXCLUDED.is_available,
                        name = EXCLUDED.name,
                        tracks_count = EXCLUDED.tracks_count,
                        likes_count = EXCLUDED.likes_count,
                        ratings_month = EXCLUDED.ratings_month,
                        cover_uri = EXCLUDED.cover_uri
                """, (
                    artist.id,
                    artist.last_month_listeners,
                    artist.last_month_listeners_delta,
                    artist.is_available,
                    artist.name,
                    artist.tracks_count,
                    artist.likes_count,
                    artist.ratings_month,
                    artist.cover_uri,
                    False,
                ))

                cur.execute("DELETE FROM artist_genres WHERE artist_id = %s", (artist.id,))
                cur.execute("DELETE FROM artist_countries WHERE artist_id = %s", (artist.id,))

                _update_artist_relations(cur, artist.id, artist.genres, artist.countries)

                conn.commit()

    def get_to_update_artists_count(self, delta_time: timedelta) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM artists
                    WHERE date_recording < NOW() - %s
                """, (delta_time,))

                return cur.fetchone()["count"]

    def get_stale_artist_ids(self, delta_time: timedelta, limit: int) -> list[int]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id
                    FROM artists
                    WHERE date_recording < NOW() - %s
                    ORDER BY date_recording ASC
                    LIMIT %s
                """, (delta_time, limit))

                return [row["id"] for row in cur.fetchall()]

    def get_artist(self, artist_id: int) -> Optional[ArtistRecord]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        a.*,
                        array_remove(array_agg(DISTINCT g.name), NULL) AS genres,
                        array_remove(array_agg(DISTINCT c.name), NULL) AS countries
                    FROM artists a
                    LEFT JOIN artist_genres ag ON a.id = ag.artist_id
                    LEFT JOIN genres g ON ag.genre_id = g.id
                    LEFT JOIN artist_countries ac ON a.id = ac.artist_id
                    LEFT JOIN countries c ON ac.country_id = c.id
                    WHERE a.id = %s
                    GROUP BY a.id
                """, (artist_id,))

                row = cur.fetchone()

                if row is None:
                    return None

                return ArtistRecord.from_dict(row)

    def artist_exists(self, artist_id: int) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM artists WHERE id = %s)",
                    (artist_id,)
                )
                return cur.fetchone()["exists"]

    def get_record_age(self, artist_id: int) -> timedelta:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT date_recording FROM artists WHERE id = %s",
                    (artist_id,)
                )

                row = cur.fetchone()

                if row is None:
                    return timedelta.max

                return datetime.now() - row["date_recording"]

    def get_all_genres(self) -> list[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name
                    FROM genres
                    ORDER BY name
                """)

                return [row["name"] for row in cur.fetchall()]

    def get_all_countries(self) -> list[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name
                    FROM countries
                    ORDER BY name
                """)

                return [row["name"] for row in cur.fetchall()]

    def get_artists_count(self, filters: Optional[dict] = None) -> int:
        base_query, where_clause, params = _build_artists_filters(filters)

        query = f"""
            SELECT COUNT(DISTINCT a.id)
            {base_query}
            {where_clause}
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()["count"]

    def get_artist_at(
            self,
            index: int,
            sort_by: str = "name",
            sort_order: str = "ASC",
            filters: Optional[dict] = None
    ) -> Optional[ArtistRecord]:

        sort_order = sort_order.upper()
        sort_order = "ASC" if sort_order not in ["ASC", "DESC"] else sort_order

        if sort_by not in VALID_SORT_FIELDS:
            sort_by = "name"

        base_query, where_clause, params = _build_artists_filters(filters)

        with self._connect() as conn:
            with conn.cursor() as cur:
                paginated_query = f"""
                    SELECT
                        a.*,
                        array_remove(array_agg(DISTINCT g.name), NULL) AS genres,
                        array_remove(array_agg(DISTINCT c.name), NULL) AS countries
                    {base_query}
                    {where_clause}
                    GROUP BY a.id
                    ORDER BY a.{sort_by} {sort_order}
                    LIMIT 1 OFFSET %s
                """

                pagination_params = params + [index]

                cur.execute(paginated_query, pagination_params)
                row = cur.fetchone()

                if row is None:
                    return None

                return ArtistRecord.from_dict(row)

    def get_artists_page(
            self,
            page: int = 1,
            page_size: int = 20,
            sort_by: str = "name",
            sort_order: str = "ASC",
            filters: Optional[dict] = None
    ) -> ArtistsPage:

        page = max(1, page)
        page_size = max(1, page_size)
        sort_order = sort_order.upper()
        sort_order = "ASC" if sort_order not in ["ASC", "DESC"] else sort_order

        if sort_by not in VALID_SORT_FIELDS:
            sort_by = "name"

        base_query, where_clause, params = _build_artists_filters(filters)

        with self._connect() as conn:
            with conn.cursor() as cur:
                count_query = f"""
                    SELECT COUNT(DISTINCT a.id)
                    {base_query}
                    {where_clause}
                """

                cur.execute(count_query, params)
                total = cur.fetchone()["count"]

                total_pages = (total + page_size - 1) // page_size if total else 0
                offset = (page - 1) * page_size

                paginated_query = f"""
                    SELECT
                        a.*,
                        array_remove(array_agg(DISTINCT g.name), NULL) AS genres,
                        array_remove(array_agg(DISTINCT c.name), NULL) AS countries
                    {base_query}
                    {where_clause}
                    GROUP BY a.id
                    ORDER BY a.{sort_by} {sort_order}
                    LIMIT %s OFFSET %s
                """

                pagination_params = params + [page_size, offset]

                cur.execute(paginated_query, pagination_params)
                rows = cur.fetchall()

                return ArtistsPage(
                    artist_records=[ArtistRecord.from_dict(row) for row in rows],
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1
                )
