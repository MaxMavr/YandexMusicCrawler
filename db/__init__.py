from datetime import datetime, timedelta
from typing import Optional

import psycopg
from psycopg import Cursor
from psycopg.rows import dict_row

from config import RepositoryConfig
from db.models import ArtistRecord, ArtistsPage

VALID_SORT_FIELDS = [
    "id", "name", "last_month_listeners", "last_month_listeners_delta",
    "tracks_count", "likes_count", "ratings_day", "ratings_month",
    "ratings_week", "is_available", "is_listened"
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


class Repository:
    def __init__(self,
                 config: RepositoryConfig):
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

                        last_month_listeners INTEGER NOT NULL,
                        last_month_listeners_delta INTEGER NOT NULL,
                        
                        tracks_count INTEGER NOT NULL,
                        likes_count INTEGER NOT NULL,
                        
                        ratings_day INTEGER NOT NULL,
                        ratings_month INTEGER NOT NULL,
                        ratings_week INTEGER NOT NULL,
                        
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
                    CREATE TABLE IF NOT EXISTS crawler_lock (
                        id BOOLEAN PRIMARY KEY DEFAULT TRUE,
                        running BOOLEAN NOT NULL DEFAULT FALSE
                    );
                    INSERT INTO crawler_lock (id, running)
                    VALUES (TRUE, FALSE)
                    ON CONFLICT (id) DO NOTHING;
                """)
            conn.commit()

    def is_crawler_running(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT running FROM crawler_lock WHERE id = TRUE")
                result = cur.fetchone()
                return result["running"] if result else False

    def try_start_crawler(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE crawler_lock
                    SET running = TRUE
                    WHERE id = TRUE AND running = FALSE
                    RETURNING running;
                """)
                result = cur.fetchone()
                return result is not None

    def stop_crawler(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE crawler_lock
                    SET running = FALSE
                    WHERE id = TRUE;
                """)

    def add_artist(
            self,
            artist: ArtistRecord,
    ) -> None:
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
                        ratings_day,
                        ratings_month,
                        ratings_week,
                        is_listened
                    )
                    VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    artist.id,
                    artist.last_month_listeners,
                    artist.last_month_listeners_delta,
                    artist.is_available,
                    artist.name,
                    artist.tracks_count,
                    artist.likes_count,
                    artist.ratings_day,
                    artist.ratings_month,
                    artist.ratings_week,
                    False,
                ))

                _update_artist_relations(cur, artist.id, artist.genres, artist.countries)

                conn.commit()

    def update_artist(
            self,
            artist: ArtistRecord,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE artists
                    SET 
                        date_recording = NOW(),
                        last_month_listeners = %s,
                        last_month_listeners_delta = %s,
                        is_available = %s,
                        tracks_count = %s,
                        likes_count = %s,
                        ratings_day = %s,
                        ratings_month = %s,
                        ratings_week = %s
                    WHERE id = %s
                """, (
                    artist.last_month_listeners,
                    artist.last_month_listeners_delta,
                    artist.is_available,
                    artist.tracks_count,
                    artist.likes_count,
                    artist.ratings_day,
                    artist.ratings_month,
                    artist.ratings_week,
                    artist.id,
                ))

                cur.execute("""
                    DELETE FROM artist_genres
                    WHERE artist_id = %s
                """, (artist.id,))

                cur.execute("""
                    DELETE FROM artist_countries
                    WHERE artist_id = %s
                """, (artist.id,))

                _update_artist_relations(cur, artist.id, artist.genres, artist.countries)

                conn.commit()

    def get_artist(
            self,
            artist_id: int,
    ) -> Optional[ArtistRecord]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT g.name
                    FROM genres g
                    JOIN artist_genres ag
                        ON ag.genre_id = g.id
                    WHERE ag.artist_id = %s
                """, (artist_id,)
                            )
                genres = [row["name"] for row in cur.fetchall()]

                cur.execute("""
                    SELECT c.name
                    FROM countries c
                    JOIN artist_countries ac
                        ON ac.country_id = c.id
                    WHERE ac.artist_id = %s 
                """, (artist_id,)
                            )
                countries = [row["name"] for row in cur.fetchall()]

                cur.execute(
                    "SELECT * FROM artists WHERE id = %s",
                    (artist_id,)
                )

                row = cur.fetchone()

                if row is None:
                    return None

                artist = ArtistRecord(
                    last_month_listeners=row["last_month_listeners"],
                    last_month_listeners_delta=row["last_month_listeners_delta"],

                    id=row["id"],
                    is_available=row["is_available"],
                    name=row["name"],

                    genres=genres,
                    countries=countries,

                    tracks_count=row["tracks_count"],
                    likes_count=row["likes_count"],

                    ratings_day=row["ratings_day"],
                    ratings_month=row["ratings_month"],
                    ratings_week=row["ratings_week"],

                    is_listened=row["is_listened"],
                )

                return artist

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

        with self._connect() as conn:
            with conn.cursor() as cur:
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
                    if "is_available" in filters:
                        if isinstance(filters["is_available"], bool):
                            where_conditions.append("a.is_available = %s")
                            params.append(filters["is_available"])

                    if "is_listened" in filters:
                        if isinstance(filters["is_listened"], bool):
                            where_conditions.append("a.is_listened = %s")
                            params.append(filters["is_listened"])

                    if "name_contains" in filters:
                        if isinstance(filters["name_contains"], str):
                            where_conditions.append("a.name ILIKE %s")
                            params.append(f"%{filters['name_contains']}%")

                    if "min_listeners" in filters:
                        if isinstance(filters["min_listeners"], int):
                            where_conditions.append("a.last_month_listeners >= %s")
                            params.append(filters["min_listeners"])

                    if "max_listeners" in filters:
                        if isinstance(filters["max_listeners"], int):
                            where_conditions.append("a.last_month_listeners <= %s")
                            params.append(filters["max_listeners"])

                    if "min_listeners_delta" in filters:
                        if isinstance(filters["min_listeners_delta"], int):
                            where_conditions.append("a.last_month_listeners_delta >= %s")
                            params.append(filters["min_listeners_delta"])

                    if "max_listeners_delta" in filters:
                        if isinstance(filters["max_listeners_delta"], int):
                            where_conditions.append("a.last_month_listeners_delta <= %s")
                            params.append(filters["max_listeners_delta"])

                    if "min_likes" in filters:
                        if isinstance(filters["min_likes"], int):
                            where_conditions.append("a.likes_count >= %s")
                            params.append(filters["min_likes"])

                    if "max_likes" in filters:
                        if isinstance(filters["max_likes"], int):
                            where_conditions.append("a.likes_count <= %s")
                            params.append(filters["max_likes"])

                    if "min_tracks" in filters:
                        if isinstance(filters["min_tracks"], int):
                            where_conditions.append("a.tracks_count >= %s")
                            params.append(filters["min_tracks"])

                    if "max_tracks" in filters:
                        if isinstance(filters["max_tracks"], int):
                            where_conditions.append("a.tracks_count <= %s")
                            params.append(filters["max_tracks"])

                    if "min_ratings_day" in filters:
                        if isinstance(filters["min_ratings_day"], int):
                            where_conditions.append("a.ratings_day >= %s")
                            params.append(filters["min_ratings_day"])

                    if "max_ratings_day" in filters:
                        if isinstance(filters["max_ratings_day"], int):
                            where_conditions.append("a.ratings_day <= %s")
                            params.append(filters["max_ratings_day"])

                    if "min_ratings_month" in filters:
                        if isinstance(filters["min_ratings_month"], int):
                            where_conditions.append("a.ratings_month >= %s")
                            params.append(filters["min_ratings_month"])

                    if "max_ratings_month" in filters:
                        if isinstance(filters["max_ratings_month"], int):
                            where_conditions.append("a.ratings_month <= %s")
                            params.append(filters["max_ratings_month"])

                    if "min_ratings_week" in filters:
                        if isinstance(filters["min_ratings_week"], int):
                            where_conditions.append("a.ratings_week >= %s")
                            params.append(filters["min_ratings_week"])

                    if "max_ratings_week" in filters:
                        if isinstance(filters["max_ratings_week"], int):
                            where_conditions.append("a.ratings_week <= %s")
                            params.append(filters["max_ratings_week"])

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

                count_query = f"""
                    SELECT COUNT(DISTINCT a.id) AS total
                    {base_query}
                    {where_clause}
                """

                cur.execute(count_query, params)
                total = cur.fetchone()["total"]

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
                    artist_records=[
                        ArtistRecord(
                            id=row["id"],
                            name=row["name"],
                            is_available=row["is_available"],
                            last_month_listeners=row["last_month_listeners"],
                            last_month_listeners_delta=row["last_month_listeners_delta"],
                            tracks_count=row["tracks_count"],
                            likes_count=row["likes_count"],
                            ratings_day=row["ratings_day"],
                            ratings_month=row["ratings_month"],
                            ratings_week=row["ratings_week"],
                            is_listened=row["is_listened"],
                            genres=row["genres"] or [],
                            countries=row["countries"] or [],
                        ) for row in rows
                    ],
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1
                )
