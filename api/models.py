from dataclasses import dataclass
from db import ArtistRecord


@dataclass
class ArtistGetResult:
    artist: ArtistRecord
    similar_artist_ids: list[int]
