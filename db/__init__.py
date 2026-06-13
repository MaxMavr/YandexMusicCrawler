from datetime import datetime, timedelta
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from db.models import ArtistRecord


class Repository:
    def __init__(
            self,
            database: str,
            user: str = "postgres",
            password: str = None,
            host: str = "localhost",
            port: int = 5432,
    ):
        self._dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
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
            conn.commit()

    def add(
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

                for genre in artist.genres:
                    cur.execute("""
                        INSERT INTO genres (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                    """, (genre,))

                    cur.execute("""
                        INSERT INTO artist_genres (
                            artist_id,
                            genre_id
                        )
                        SELECT %s, id
                        FROM genres
                        WHERE name = %s
                        ON CONFLICT DO NOTHING
                    """, (artist.id, genre))

                for country in artist.countries:
                    cur.execute("""
                        INSERT INTO countries (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                    """, (country,))

                    cur.execute("""
                        INSERT INTO artist_countries (
                            artist_id,
                            country_id
                        )
                        SELECT %s, id
                        FROM countries
                        WHERE name = %s
                        ON CONFLICT DO NOTHING
                    """, (artist.id, country))

    def upd(
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

                for genre in artist.genres:
                    cur.execute("""
                        INSERT INTO genres (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                    """, (genre,))

                    cur.execute("""
                        INSERT INTO artist_genres (
                            artist_id,
                            genre_id
                        )
                        SELECT %s, id
                        FROM genres
                        WHERE name = %s
                        ON CONFLICT DO NOTHING
                    """, (artist.id, genre))

                for country in artist.countries:
                    cur.execute("""
                        INSERT INTO countries (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                    """, (country,))

                    cur.execute("""
                        INSERT INTO artist_countries (
                            artist_id,
                            country_id
                        )
                        SELECT %s, id
                        FROM countries
                        WHERE name = %s
                        ON CONFLICT DO NOTHING
                    """, (artist.id, country))

    def get(
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
                )

                return artist

    def exists(self, artist_id: int) -> bool:
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
                    return timedelta(days=365 * 5_000_000_000)

                return datetime.now() - row["date_recording"]
